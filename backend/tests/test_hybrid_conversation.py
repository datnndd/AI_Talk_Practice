import pytest

from app.infra.contracts import Message
from app.infra.factory import ConversationLLMClients
from app.modules.sessions.services.hybrid_conversation.analysis_service import LLMTurnAnalysisService
from app.modules.sessions.services.hybrid_conversation.analyzer import TopicAnalyzer
from app.modules.sessions.services.hybrid_conversation.fact_extractor import RuleBasedFactExtractor
from app.modules.sessions.services.hybrid_conversation.memory import SessionMemoryManager
from app.modules.sessions.services.hybrid_conversation.orchestrator import DialogueOrchestrator
from app.modules.sessions.services.hybrid_conversation.prompt_builder import PromptBuilder
from app.modules.sessions.services.hybrid_conversation.response_policy import ResponsePolicy
from app.modules.sessions.services.hybrid_conversation.schemas import (
    DialogueState,
    PolicyAction,
    RepairAction,
    ScenarioDefinition,
    ScenarioObjective,
    ScenarioPhase,
    SessionMemory,
    TurnLabel,
)
from app.modules.sessions.services.hybrid_conversation.state_controller import DialogueStateController


class FakeLLM:
    def __init__(self, chunks=None):
        self.calls = []
        self.chunks = chunks or ["Sure, ", "what document do you need help with?"]

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": [(message.role, message.content) for message in messages],
                "max_tokens": max_tokens,
            }
        )
        for chunk in self.chunks:
            yield chunk


def coworker_scenario() -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id="coworker-help",
        title="Ask a coworker for help",
        description="Practice asking a coworker for help with a document.",
        user_role="Employee",
        ai_role="Helpful coworker",
        objective="Ask for help writing a work document and clarify what you need.",
        allowed_topic_boundaries=[
            "coworker help",
            "writing a document",
            "work task",
            "deadline",
            "clarifying help needed",
        ],
        phases=[
            ScenarioPhase(
                phase_id="greeting",
                title="Greeting",
                objective="Open the conversation and state the need.",
                starting_question="Hi, what do you need help with today?",
                expected_intents=["ask for help", "state need"],
            ),
            ScenarioPhase(
                phase_id="details",
                title="Details",
                objective="Clarify the document and deadline.",
                starting_question="What kind of document is it?",
                expected_intents=["clarify document", "deadline"],
            ),
        ],
        speaking_style="friendly and concise",
        difficulty="medium",
        expected_intents=["ask for help", "clarify document", "confirm next step"],
        target_vocabulary=["document", "deadline", "draft"],
        target_functions=["ask for help", "give context"],
        opening_message="Hi, what do you need help with today?",
        objectives=[
            ScenarioObjective(objective_id="ask_for_help", goal="Ask for help writing a work document"),
            ScenarioObjective(objective_id="clarify_need", goal="Clarify what kind of help is needed"),
            ScenarioObjective(objective_id="confirm_next_step", goal="Confirm the next step"),
        ],
    )


def coffee_scenario() -> ScenarioDefinition:
    return ScenarioDefinition(
        scenario_id="morning-brew",
        title="Morning Brew",
        description="Practice ordering coffee at a cafe.",
        user_role="Customer",
        ai_role="Barista",
        objective="Order a drink and ask simple menu details.",
        allowed_topic_boundaries=["coffee shop", "ordering drinks", "menu", "price", "ingredients"],
        phases=[
            ScenarioPhase(
                phase_id="greeting",
                title="Greeting",
                objective="Ask what the customer wants to order.",
                starting_question="What kind of coffee can I get for you today?",
                expected_intents=["order a drink"],
            )
        ],
        target_vocabulary=["coffee", "latte", "cappuccino", "espresso", "iced", "hot"],
        target_functions=["order a drink", "ask about menu"],
        opening_message="Welcome to Morning Brew. What can I get for you?",
        objectives=[
            ScenarioObjective(objective_id="order_drink", goal="Order a drink"),
            ScenarioObjective(objective_id="ask_menu", goal="Ask a simple menu detail"),
        ],
    )


def test_fact_extractor_extracts_relevant_short_term_facts():
    extractor = RuleBasedFactExtractor()

    facts = extractor.extract(
        "I'm a designer, I like coffee, I'm nervous about the interview, and I need help writing this document.",
        turn_index=3,
    )
    by_key = {fact.key: fact.value for fact in facts}

    assert by_key["profession"] == "designer"
    assert by_key["likes"] == "coffee"
    assert by_key["concern"] == "nervous about the interview"
    assert by_key["need"] == "help writing this document"
    assert all(fact.source_turn_index == 3 for fact in facts)


def test_memory_upserts_prunes_and_exports_compact_facts():
    memory = SessionMemory(
        scenario_id="coworker-help",
        current_objective="Ask for help with a document",
        current_phase_id="greeting",
    )
    manager = SessionMemoryManager(memory, max_facts=2, recent_turn_limit=2, summary_max_chars=120)
    extractor = RuleBasedFactExtractor()

    manager.update_facts(extractor.extract("I'm a designer.", turn_index=1))
    manager.update_facts(extractor.extract("I like coffee.", turn_index=2))
    manager.update_facts(extractor.extract("I'm a product designer.", turn_index=3))
    manager.record_turn(user_text="I need help writing this document.", assistant_text="What kind of document?", turn_index=3)

    compact = manager.compact_export()

    assert len(manager.memory.facts) == 2
    assert "profession: product designer" in compact["facts"]
    assert "likes: coffee" in compact["facts"]
    assert "I need help writing this document." in compact["recent_turns"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("I need help writing this document.", TurnLabel.ON_TOPIC),
        ("I like coffee by the way.", TurnLabel.PARTIALLY_ON_TOPIC),
        ("My cat likes dancing on the moon.", TurnLabel.OFF_TOPIC),
        ("asdf qwer zzzz", TurnLabel.NONSENSE),
        ("yes", TurnLabel.TOO_SHORT),
        ("Can you give me a hint?", TurnLabel.HELP_REQUEST),
        ("What do you mean?", TurnLabel.CLARIFICATION_REQUEST),
    ],
)
def test_topic_analyzer_returns_structured_labels(text, expected):
    scenario = coworker_scenario()
    state = DialogueState(scenario_id=scenario.scenario_id, current_phase_id="greeting")
    facts = RuleBasedFactExtractor().extract(text, turn_index=1)

    analysis = TopicAnalyzer().analyze(text, scenario=scenario, state=state, extracted_facts=facts)

    assert analysis.label == expected
    assert expected in analysis.labels


@pytest.mark.parametrize("text", ["A latte please.", "Cappuccino.", "Iced coffee with oat milk."])
def test_topic_analyzer_accepts_short_cafe_order_answers(text):
    scenario = coffee_scenario()
    state = DialogueState(scenario_id=scenario.scenario_id, current_phase_id="greeting")

    analysis = TopicAnalyzer().analyze(text, scenario=scenario, state=state, extracted_facts=[])

    assert analysis.label == TurnLabel.ON_TOPIC
    assert analysis.contains_direct_answer is True


def test_state_controller_advances_on_useful_answer_and_repairs_low_quality_turns():
    scenario = coworker_scenario()
    state = DialogueState(scenario_id=scenario.scenario_id, current_phase_id="greeting")
    analyzer = TopicAnalyzer()
    controller = DialogueStateController()

    useful = analyzer.analyze(
        "I need help writing this document.",
        scenario=scenario,
        state=state,
        extracted_facts=[],
    )
    advanced = controller.apply_turn(state, scenario=scenario, analysis=useful)

    assert advanced.current_phase_id == "details"
    assert advanced.turn_index == 1
    assert advanced.repair_count == 0

    short = analyzer.analyze("yes", scenario=scenario, state=advanced, extracted_facts=[])
    repaired = controller.apply_turn(advanced, scenario=scenario, analysis=short)

    assert repaired.current_phase_id == "details"
    assert repaired.repair_count == 1


def test_prompt_builder_uses_compact_context_without_full_transcript():
    scenario = coworker_scenario()
    memory = SessionMemory(
        scenario_id=scenario.scenario_id,
        current_objective=scenario.objective,
        current_phase_id="greeting",
        recent_dialogue_summary="The learner asked for help with a document.",
    )
    manager = SessionMemoryManager(memory, max_facts=5, recent_turn_limit=2, summary_max_chars=120)
    manager.update_facts(RuleBasedFactExtractor().extract("I'm a designer.", turn_index=1))

    system_prompt, messages = PromptBuilder().build(
        scenario=scenario,
        memory=memory,
        state=DialogueState(scenario_id=scenario.scenario_id, current_phase_id="greeting"),
        user_text="I need help with the draft.",
        repair_action=RepairAction(action=PolicyAction.GENERATE, reason="on_topic"),
    )

    prompt_text = system_prompt + "\n" + "\n".join(message.content for message in messages)
    assert "Ask a coworker for help" in prompt_text
    assert "profession: designer" in prompt_text
    assert "one focused question" in prompt_text
    assert "old raw turn that should not be included" not in prompt_text
    assert messages == [Message(role="user", content="I need help with the draft.")]


@pytest.mark.parametrize(
    ("text", "expected_action"),
    [
        ("asdf qwer zzzz", PolicyAction.REASK),
        ("yes", PolicyAction.NARROW_QUESTION),
        ("Can you give me a hint?", PolicyAction.HINT),
        ("My cat likes dancing on the moon.", PolicyAction.REDIRECT),
        ("I like coffee by the way.", PolicyAction.ACKNOWLEDGE_AND_STEER),
    ],
)
def test_response_policy_selects_repair_actions(text, expected_action):
    scenario = coworker_scenario()
    state = DialogueState(scenario_id=scenario.scenario_id, current_phase_id="greeting")
    facts = RuleBasedFactExtractor().extract(text, turn_index=1)
    analysis = TopicAnalyzer().analyze(text, scenario=scenario, state=state, extracted_facts=facts)

    action = ResponsePolicy().decide(analysis, scenario=scenario, state=state)

    assert action.action == expected_action


@pytest.mark.asyncio
async def test_orchestrator_stores_side_fact_repairs_and_uses_compact_llm_prompt():
    scenario = coworker_scenario()
    llm = FakeLLM()
    orchestrator = DialogueOrchestrator.create(
        scenario=scenario,
        llm=llm,
        max_facts=5,
        recent_turn_limit=3,
        summary_max_chars=240,
        repair_max_repeats=2,
    )

    coffee_reply = "".join([chunk async for chunk in orchestrator.stream_turn("I like coffee by the way.")])
    nonsense_reply = "".join([chunk async for chunk in orchestrator.stream_turn("asdf qwer zzzz")])
    llm_reply = "".join([chunk async for chunk in orchestrator.stream_turn("I need help writing this document.")])

    assert "coffee" in orchestrator.memory.compact_export()["facts"]
    assert "today" in coffee_reply.lower() or "need help" in coffee_reply.lower()
    assert "say that again" in nonsense_reply.lower() or "try again" in nonsense_reply.lower()
    assert llm_reply == "Sure, what document do you need help with?"
    assert len(llm.calls) == 1
    assert llm.calls[0]["messages"] == [("user", "I need help writing this document.")]
    assert "I like coffee by the way." not in llm.calls[0]["messages"][0][1]


@pytest.mark.asyncio
async def test_llm_turn_analysis_uses_rule_result_without_llm_for_confident_turn():
    scenario = coworker_scenario()
    state = DialogueState(scenario_id=scenario.scenario_id, current_phase_id="greeting")
    analysis_llm = FakeLLM(chunks=['{"label":"off_topic","relevance_score":0.0}'])
    service = LLMTurnAnalysisService(
        llm=analysis_llm,
        analyzer=TopicAnalyzer(),
        enable_llm_relevance=False,
        enable_llm_fact_extraction=False,
    )

    analysis, facts = await service.analyze(
        "I need help writing this document.",
        scenario=scenario,
        state=state,
        rule_facts=[],
    )

    assert analysis.label == TurnLabel.ON_TOPIC
    assert facts == []
    assert analysis_llm.calls == []


@pytest.mark.asyncio
async def test_llm_turn_analysis_enriches_gray_zone_and_falls_back_on_bad_json():
    scenario = coworker_scenario()
    state = DialogueState(scenario_id=scenario.scenario_id, current_phase_id="greeting")
    analysis_llm = FakeLLM(
        chunks=[
            '{"label":"on_topic","relevance_score":0.82,"confidence":0.91,'
            '"contains_direct_answer":true,"intent":"ask for help",'
            '"useful_facts":[{"key":"need","value":"help with a project brief",'
            '"category":"goal","confidence":0.88,"relevance_to_scenario":0.9}],'
            '"corrected_text":"I need help with a project brief.",'
            '"explanation":"Add help with to make the request natural.",'
            '"completed_objective_ids":["ask_for_help"],'
            '"objective_confidences":{"ask_for_help":0.92},'
            '"repair_reason":"answers active phase"}'
        ]
    )
    service = LLMTurnAnalysisService(
        llm=analysis_llm,
        analyzer=TopicAnalyzer(on_topic_threshold=0.6, partial_threshold=0.2),
        enable_llm_relevance=True,
        enable_llm_fact_extraction=True,
    )

    analysis, facts = await service.analyze(
        "I need a project brief.",
        scenario=scenario,
        state=state,
        rule_facts=[],
    )

    assert analysis.label == TurnLabel.ON_TOPIC
    assert analysis.relevance_score == 0.82
    assert analysis.contains_direct_answer is True
    assert analysis.corrected_text == "I need help with a project brief."
    assert analysis.explanation == "Add help with to make the request natural."
    assert analysis.completed_objective_ids == ["ask_for_help"]
    assert analysis.objective_confidences == {"ask_for_help": 0.92}
    assert facts[0].key == "need"
    assert facts[0].value == "help with a project brief"
    assert analysis_llm.calls

    broken_llm = FakeLLM(chunks=["not json"])
    broken_service = LLMTurnAnalysisService(
        llm=broken_llm,
        analyzer=TopicAnalyzer(on_topic_threshold=0.6, partial_threshold=0.2),
        enable_llm_relevance=True,
        enable_llm_fact_extraction=False,
    )

    fallback, fallback_facts = await broken_service.analyze(
        "I need a project brief.",
        scenario=scenario,
        state=state,
        rule_facts=[],
    )

    assert fallback.label in {TurnLabel.PARTIALLY_ON_TOPIC, TurnLabel.OFF_TOPIC}
    assert fallback_facts == []


def test_state_controller_tracks_objective_progress_and_closing_mode():
    scenario = coworker_scenario()
    controller = DialogueStateController()
    state = DialogueState(scenario_id=scenario.scenario_id, current_phase_id="greeting")

    first = TopicAnalyzer().analyze(
        "I need help writing this document.",
        scenario=scenario,
        state=state,
        extracted_facts=[],
    ).model_copy(update={"completed_objective_ids": ["ask_for_help", "clarify_need"]})

    advanced = controller.apply_turn(state, scenario=scenario, analysis=first)
    progress = advanced.objective_progress(total_objectives=len(scenario.objectives))

    assert advanced.completed_objective_ids == ["ask_for_help", "clarify_need"]
    assert progress.completed == 2
    assert progress.percent == 67
    assert advanced.closing_mode is False

    second = first.model_copy(update={"completed_objective_ids": ["confirm_next_step"]})
    completed = controller.apply_turn(advanced, scenario=scenario, analysis=second)
    final_progress = completed.objective_progress(total_objectives=len(scenario.objectives))

    assert completed.closing_mode is True
    assert completed.should_end is True
    assert completed.end_reason == "scenario_objective_completed"
    assert final_progress.percent == 100


@pytest.mark.asyncio
async def test_orchestrator_routes_analysis_and_dialogue_to_separate_llms():
    scenario = coworker_scenario()
    analysis_llm = FakeLLM(chunks=['{"label":"off_topic","relevance_score":0.0}'])
    dialogue_llm = FakeLLM(chunks=["Dialogue reply."])
    evaluation_llm = FakeLLM(chunks=["unused"])
    orchestrator = DialogueOrchestrator.create(
        scenario=scenario,
        llm_clients=ConversationLLMClients(
            analysis=analysis_llm,
            dialogue=dialogue_llm,
            evaluation=evaluation_llm,
        ),
        max_facts=5,
        recent_turn_limit=3,
        summary_max_chars=240,
        repair_max_repeats=2,
        enable_llm_relevance_analysis=False,
        enable_llm_fact_extraction=False,
    )

    reply = "".join([chunk async for chunk in orchestrator.stream_turn("I need help writing this document.")])

    assert reply == "Dialogue reply."
    assert analysis_llm.calls == []
    assert len(dialogue_llm.calls) == 1
    assert evaluation_llm.calls == []

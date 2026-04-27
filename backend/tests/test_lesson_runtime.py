import json

import pytest

from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.services.lesson_runtime import LessonRuntimeService


class HintLLM:
    def __init__(self, response):
        self.response = response
        self.calls = []
        self._config = type("Config", (), {"lesson_hint_llm_max_tokens": 700})()

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": [(message.role, message.content) for message in messages],
                "max_tokens": max_tokens,
            }
        )
        yield self.response


def make_scenario(*, tasks=None):
    return Scenario(
        id=123,
        title="Restaurant roleplay",
        description="Order a meal and respond politely.",
        tasks=tasks or ["ordering food", "asking for the bill"],
        ai_system_prompt="You are a waiter.",
        ai_role="Polite waiter",
        category="daily-life",
        difficulty="easy",
    )


def test_lesson_runtime_generates_package_and_advances():
    scenario = make_scenario()
    package = LessonRuntimeService.create_lesson_package(scenario=scenario, level="beginner")
    state = LessonRuntimeService.initial_state(package)

    assert package.lesson_id
    assert len(package.objectives) == 2
    assert state.last_question == package.objectives[0].main_question
    assert "I will start" not in package.objectives[0].main_question
    assert "what would you say first" not in package.objectives[0].main_question.lower()
    assert "Practice " not in package.objectives[0].main_question

    first_result = LessonRuntimeService.advance(
        scenario=scenario,
        session_id=99,
        package=package,
        state=state,
        user_answer="I would like to order food for my table today, please.",
    )

    assert first_result.state.progress.completed == 1
    assert first_result.state.current_objective.objective_id == "obj_2"
    assert first_result.assistant_text == package.objectives[1].main_question

    second_result = LessonRuntimeService.advance(
        scenario=scenario,
        session_id=99,
        package=package,
        state=state,
        user_answer="Could I ask for the bill now, please? Thank you very much.",
    )

    assert second_result.state.status == "completed"
    assert second_result.state.should_end is True
    assert second_result.state.end_reason == "all_objectives_completed"
    assert "Session summary:" in second_result.assistant_text
    assert "Goals achieved:" in second_result.assistant_text


def test_lesson_hint_fallback_explains_current_question():
    scenario = make_scenario(tasks=["ordering food"])
    package = LessonRuntimeService.create_lesson_package(scenario=scenario, level="beginner")
    state = LessonRuntimeService.initial_state(package)
    state.last_question = "What would you like to order today?"

    hint = LessonRuntimeService.build_hint(
        package=package,
        state=state,
        user_last_answer=None,
    )

    assert hint.lesson_id == package.lesson_id
    assert hint.objective_id == package.objectives[0].objective_id
    assert hint.question == "What would you like to order today?"
    assert hint.keywords
    assert "AI dang hoi" in hint.analysis_vi
    assert "Tra loi toi da" in hint.answer_strategy_vi
    assert hint.sample_answers


@pytest.mark.asyncio
async def test_lesson_hint_dynamic_sends_current_question_to_llm():
    scenario = make_scenario(tasks=["ordering food"])
    package = LessonRuntimeService.create_lesson_package(scenario=scenario, level="beginner")
    state = LessonRuntimeService.initial_state(package)
    state.last_question = "Would you like that hot or iced?"
    llm = HintLLM(json.dumps({
        "question_analysis_vi": "AI dang hoi ban muon mon do nong hay lanh.",
        "answer_strategy_vi": "Chon mot lua chon, sau do noi them kich co hoac so thich.",
        "keywords": ["hot", "iced", "regular"],
        "sample_answers": [
            "I would like it iced, please.",
            "Hot is fine, and I would like a regular size.",
        ],
        "simple_answer": "Iced, please.",
    }))

    hint = await LessonRuntimeService.build_hint_dynamic(
        scenario=scenario,
        package=package,
        state=state,
        llm=llm,
    )

    assert hint.question == "Would you like that hot or iced?"
    assert hint.analysis_vi == "AI dang hoi ban muon mon do nong hay lanh."
    assert hint.sample_answers == [
        "I would like it iced, please.",
        "Hot is fine, and I would like a regular size.",
    ]
    assert hint.sample_answer == "I would like it iced, please."
    assert hint.sample_answer_easy == "Iced, please."
    assert llm.calls[0]["max_tokens"] == 700
    assert "Would you like that hot or iced?" in llm.calls[0]["messages"][0][1]


@pytest.mark.asyncio
async def test_lesson_hint_dynamic_invalid_json_can_fallback():
    scenario = make_scenario(tasks=["ordering food"])
    package = LessonRuntimeService.create_lesson_package(scenario=scenario, level="beginner")
    state = LessonRuntimeService.initial_state(package)
    state.last_question = "What would you like to order today?"
    llm = HintLLM("not json")

    with pytest.raises(ValueError):
        await LessonRuntimeService.build_hint_dynamic(
            scenario=scenario,
            package=package,
            state=state,
            llm=llm,
        )

    fallback = LessonRuntimeService.build_hint(
        package=package,
        state=state,
        user_last_answer=None,
    )
    assert fallback.question == "What would you like to order today?"
    assert fallback.sample_answer


def test_lesson_hint_cache_key_uses_question_and_follow_up_index():
    scenario = make_scenario(tasks=["ordering food"])
    package = LessonRuntimeService.create_lesson_package(scenario=scenario, level="beginner")
    state = LessonRuntimeService.initial_state(package)
    state.last_question = "What would you like to order today?"
    hint = LessonRuntimeService.build_hint(package=package, state=state, user_last_answer=None)

    hints = LessonRuntimeService.store_hint(
        hints={},
        objective_id=hint.objective_id,
        question=hint.question,
        payload=hint,
        follow_up_index=0,
    )

    assert LessonRuntimeService.get_cached_hint(
        hints=hints,
        objective_id=hint.objective_id,
        question="What would you like to order today?",
        follow_up_index=0,
    )
    assert LessonRuntimeService.get_cached_hint(
        hints=hints,
        objective_id=hint.objective_id,
        question="Would you like that hot or iced?",
        follow_up_index=0,
    ) is None
    assert LessonRuntimeService.get_cached_hint(
        hints=hints,
        objective_id=hint.objective_id,
        question="What would you like to order today?",
        follow_up_index=1,
    ) is None


def test_lesson_package_uses_prompt_generated_goals_by_level():
    scenario = make_scenario(
        tasks=[
            "Professional vocabulary",
            "past tense narration",
            "expressing strengths and experience",
        ],
    )
    scenario.title = "Job Interview - Tell Me About Yourself"
    scenario.category = "business"
    scenario.ai_role = "Hiring manager"
    scenario.ai_system_prompt = "You are an interviewer hiring a candidate. Ask one question at a time."
    plan = {
        "opening_message": "Welcome. Could you introduce yourself and explain what role you want?",
        "goals": [
            {
                "goal": "Introduce background",
                "question": "What background should I know about?",
                "success_criteria": ["target role", "relevant experience"],
                "follow_up_questions": ["What experience is most relevant?"],
                "vocabulary": ["target role", "relevant experience"],
            },
            {
                "goal": "Describe an achievement",
                "question": "Tell me about a useful achievement.",
                "success_criteria": ["project", "result"],
                "follow_up_questions": ["What was the result?"],
                "vocabulary": ["project", "result"],
            },
            {
                "goal": "Explain a strength",
                "question": "What strength would you bring?",
                "success_criteria": ["strength", "example"],
                "follow_up_questions": ["Can you give an example?"],
                "vocabulary": ["strength", "example"],
            },
            {
                "goal": "Explain fit",
                "question": "Why are you interested in this role?",
                "success_criteria": ["role fit", "growth"],
                "follow_up_questions": ["How do you want to grow?"],
                "vocabulary": ["role fit", "growth"],
            },
        ],
    }

    beginner_package = LessonRuntimeService.create_lesson_package_from_plan(
        scenario=scenario,
        level="beginner",
        plan=plan,
    )
    advanced_package = LessonRuntimeService.create_lesson_package_from_plan(
        scenario=scenario,
        level="advanced",
        plan=plan,
    )

    assert len(beginner_package.objectives) == 2
    assert len(advanced_package.objectives) == 4
    assert advanced_package.objectives[0].main_question == plan["opening_message"]
    assert advanced_package.objectives[0].expected_points == ["target role", "relevant experience"]
    assert advanced_package.objectives[0].follow_up_questions == ["What experience is most relevant?"]


def test_lesson_package_uses_prompt_generated_useful_phrases():
    scenario = make_scenario()
    plan = {
        "opening_message": "Good morning. What can I get started for you?",
        "goals": [
            {
                "goal": "Order a drink",
                "starting_question": "What can I get started for you?",
                "success_criteria": ["drink order", "menu detail"],
                "follow_up_questions": ["Would you like that hot or iced?"],
                "useful_phrases": ["I'd like a latte", "What's in this?", "How much is it?"],
            }
        ],
    }

    package = LessonRuntimeService.create_lesson_package_from_plan(
        scenario=scenario,
        level="beginner",
        plan=plan,
    )

    assert package.objectives[0].hint_seed.grammar == "I'd like a latte, What's in this?, How much is it?"


def test_prompt_generated_follow_up_avoids_generic_teacher_prompt():
    scenario = make_scenario(
        tasks=["Professional vocabulary"],
    )
    scenario.title = "Job Interview - Tell Me About Yourself"
    scenario.category = "business"
    scenario.ai_role = "Hiring manager"
    scenario.ai_system_prompt = "You are an interviewer hiring a candidate."
    plan = {
        "opening_message": "Welcome. What role are you interviewing for?",
        "goals": [
            {
                "goal": "Introduce background",
                "question": "What background should I know about?",
                "success_criteria": ["target role", "relevant experience"],
                "follow_up_questions": ["Which responsibility is closest to this role?"],
                "vocabulary": ["target role", "relevant experience", "responsibility"],
            }
        ],
    }

    package = LessonRuntimeService.create_lesson_package_from_plan(scenario=scenario, level="advanced", plan=plan)
    state = LessonRuntimeService.initial_state(package)
    result = LessonRuntimeService.advance(
        scenario=scenario,
        session_id=99,
        package=package,
        state=state,
        user_answer="I worked in software for three years.",
    )

    assert "Good start" not in result.assistant_text
    assert "professional vocabulary" not in result.assistant_text.lower()
    assert result.assistant_text == "Which responsibility is closest to this role?"


def test_meta_opening_from_plan_is_replaced_with_roleplay_line():
    scenario = make_scenario()
    plan = {
        "opening_message": (
            "Practice ordering drinks, asking about the menu, and making small talk with a barista. "
            "I will start the conversation: what would you say first?"
        ),
        "goals": [
            {
                "goal": "Order a drink",
                "question": "Practice ordering a drink.",
                "success_criteria": ["drink order", "polite request"],
                "follow_up_questions": ["Would you like that hot or iced?"],
                "vocabulary": ["drink order", "polite request"],
            }
        ],
    }

    package = LessonRuntimeService.create_lesson_package_from_plan(
        scenario=scenario,
        level="beginner",
        plan=plan,
    )

    opening = package.objectives[0].main_question
    assert "Practice ordering" not in opening
    assert "I will start" not in opening
    assert "what would you say first" not in opening.lower()
    assert opening == "Hello! How can I help you today?"


def test_fallback_contextualizes_vague_vocabulary_objectives():
    scenario = make_scenario(
        tasks=["Professional vocabulary"],
    )
    scenario.title = "Job Interview - Tell Me About Yourself"
    scenario.category = "business"
    scenario.description = "Introduce yourself to a hiring manager for a product role."
    scenario.ai_role = "Hiring manager"
    scenario.ai_system_prompt = "You are an interviewer hiring a candidate."

    package = LessonRuntimeService.create_lesson_package(scenario=scenario, level="beginner")
    state = LessonRuntimeService.initial_state(package)
    state_read = LessonRuntimeService.build_state_read(
        session_id=99,
        scenario=scenario,
        package=package,
        state=state,
    )

    assert package.objectives[0].goal == "Use precise phrases for Job Interview - Tell Me About Yourself"
    assert "professional vocabulary" not in package.objectives[0].goal.lower()
    assert state_read.lesson_goals == ["Use precise phrases for Job Interview - Tell Me About Yourself"]
    assert package.objectives[0].expected_points

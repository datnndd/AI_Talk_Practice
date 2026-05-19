from types import SimpleNamespace

from app.modules.sessions.services.conversation_prompts import (
    build_dialogue_system_prompt,
    build_full_assessment_prompt,
    build_hint_prompt,
    build_realtime_correction_prompt,
    build_summary_prompt,
)


def _scenario():
    return SimpleNamespace(
        title="Coffee Shop Delay",
        description="Ask politely about a delayed coffee order.",
        user_role="Customer",
        ai_role="Barista",
        tasks=["Ask for an update", "Stay polite"],
        ai_system_prompt="Stay warm and concise.",
    )


def test_dialogue_prompt_includes_roles_summary_and_recent_turns():
    prompt = build_dialogue_system_prompt(
        scenario=_scenario(),
        rolling_summary="Learner already greeted the barista.",
        recent_turns="Learner: Hi, my drink is late.\nAssistant: Let me check your order.",
        learner_profile={"favorite_topics": ["coffee"], "level": "A1"},
        extra_instruction="Trả lời lịch sự, khép lại cuộc trò chuyện một cách tự nhiên",
    )

    assert "Learner onboarding profile:" in prompt
    assert "coffee" in prompt
    assert "A1" in prompt
    assert "AI role: Barista" in prompt
    assert "Learner role: Customer" in prompt
    assert "Ask for an update" in prompt
    assert "Rolling session summary: Learner already greeted the barista." in prompt
    assert "Recent turns:" in prompt
    assert "Trả lời lịch sự, khép lại cuộc trò chuyện một cách tự nhiên" in prompt
    assert "[[SESSION_END=yes]]" in prompt
    assert "[[SESSION_END=no]]" in prompt
    assert "Never mention, explain, or reference the marker" in prompt
    assert "Do not use clipped or telegraphic fragments" in prompt
    assert "What coffee?" in prompt
    assert "Sure, one coffee. What size would you like: small, medium, or large?" in prompt


def test_summary_prompt_has_json_contract_and_context():
    prompt = build_summary_prompt(
        scenario=_scenario(),
        previous_summary="The learner said hello.",
        recent_turns="Learner: Is my coffee ready?\nAssistant: Let me check.",
    )

    assert "Return only one JSON object" in prompt
    assert '"summary"' in prompt
    assert "Previous summary: The learner said hello." in prompt
    assert "Recent turns:" in prompt


def test_realtime_correction_prompt_focuses_on_grammar_and_clarity_json():
    prompt = build_realtime_correction_prompt(
        scenario_title="Coffee Shop Delay",
        text="I wait coffee long time.",
    )

    assert "Decide if the answer is good enough" in prompt
    assert "I wait coffee long time." in prompt
    assert '"is_good"' in prompt
    assert '"better_answer"' in prompt


def test_hint_prompt_returns_lesson_hint_shape():
    prompt = build_hint_prompt(
        scenario=_scenario(),
        rolling_summary="The learner is waiting for the drink.",
        recent_turns="Learner: Hi.\nAssistant: How can I help you with your order?",
        current_question="How can I help you with your order?",
        user_text=None,
    )

    assert '"hint1"' in prompt
    assert '"hint2"' in prompt
    assert '"hint3"' in prompt
    assert "Current question: How can I help you with your order?" in prompt
    assert "Rolling summary:" not in prompt


def test_full_assessment_prompt_includes_score_contract():
    prompt = build_full_assessment_prompt(
        scenario_title="Coffee Shop Delay",
        scenario_description="Ask politely about a delayed coffee order.",
        tasks=["ask for update"],
        rolling_summary="Learner asked politely and clarified the order.",
    )

    assert "Use numeric scores from 0 to 10." in prompt
    assert "pronunciation" not in prompt.lower()
    assert "objective_completion" in prompt
    assert '"objective_completion": "completed|not_completed"' in prompt
    assert "completed|partial|not_completed" not in prompt
    assert "feedback_summary" in prompt



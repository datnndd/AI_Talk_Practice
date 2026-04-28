from types import SimpleNamespace

from app.modules.sessions.services.conversation_prompts import (
    build_conversation_end_check_prompt,
    build_dialogue_system_prompt,
    build_full_assessment_prompt,
    build_hint_prompt,
    build_personal_info_extraction_prompt,
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
        user_preferences={"favorite_topics": ["coffee"]},
        extra_instruction="Trả lời lịch sự, khép lại cuộc trò chuyện một cách tự nhiên",
    )

    assert "Stay warm and concise." in prompt
    assert "AI role: Barista" in prompt
    assert "Learner role: Customer" in prompt
    assert "Ask for an update" in prompt
    assert "Rolling session summary: Learner already greeted the barista." in prompt
    assert "Recent turns:" in prompt
    assert "Trả lời lịch sự, khép lại cuộc trò chuyện một cách tự nhiên" in prompt


def test_summary_prompt_has_json_contract_and_length_limit():
    prompt = build_summary_prompt(
        scenario=_scenario(),
        previous_summary="The learner said hello.",
        recent_turns="Learner: Is my coffee ready?\nAssistant: Let me check.",
        max_chars=500,
    )

    assert "Return only one JSON object" in prompt
    assert '"summary"' in prompt
    assert "Keep the summary under 500 characters" in prompt


def test_realtime_correction_prompt_focuses_on_grammar_and_clarity_json():
    prompt = build_realtime_correction_prompt(
        scenario_title="Coffee Shop Delay",
        text="I wait coffee long time.",
    )

    assert "Focus on grammar, vocabulary choice, and naturalness" in prompt
    assert "I wait coffee long time." in prompt
    assert '"corrected_text"' in prompt
    assert '"corrections"' in prompt


def test_hint_prompt_returns_lesson_hint_shape():
    prompt = build_hint_prompt(
        scenario=_scenario(),
        rolling_summary="The learner is waiting for the drink.",
        recent_turns="Learner: Hi.\nAssistant: How can I help you with your order?",
        current_question="How can I help you with your order?",
        user_text=None,
    )

    assert "analysis_vi" in prompt
    assert "answer_strategy_vi" in prompt
    assert "sample_answer_easy" in prompt
    assert "Current question or last assistant prompt: How can I help you with your order?" in prompt


def test_full_assessment_prompt_includes_score_contract():
    prompt = build_full_assessment_prompt(
        scenario_title="Coffee Shop Delay",
        scenario_description="Ask politely about a delayed coffee order.",
        tasks=["ask for update"],
        rolling_summary="Learner asked politely and clarified the order.",
    )

    assert "Use numeric scores from 0 to 10." in prompt
    assert "pronunciation_score" in prompt
    assert "objective_completion" in prompt
    assert "feedback_summary" in prompt


def test_personal_info_prompt_collects_preferences_and_personal_info():
    prompt = build_personal_info_extraction_prompt(
        existing_preferences={"favorite_topics": ["travel"]},
    )

    assert "Existing preferences snapshot" in prompt
    assert '"personal_info"' in prompt
    assert '"preferences"' in prompt
    assert '"notes"' in prompt


def test_conversation_end_check_prompt_requires_yes_no_json_decision():
    prompt = build_conversation_end_check_prompt(
        scenario=_scenario(),
        recent_turns="Learner: Thanks for your help.\nAssistant: You're welcome.\nLearner: Goodbye.",
    )

    assert "Return only one JSON object" in prompt
    assert "Answer yes only if the learner is clearly trying to close the conversation" in prompt
    assert '"should_end":"yes|no"' in prompt

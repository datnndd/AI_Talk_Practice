from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.services.lesson_runtime import LessonRuntimeService


def make_scenario(*, learning_objectives=None, metadata=None):
    return Scenario(
        id=123,
        title="Restaurant roleplay",
        description="Order a meal and respond politely.",
        learning_objectives=learning_objectives or ["ordering food", "asking for the bill"],
        ai_system_prompt="You are a waiter.",
        category="daily-life",
        difficulty="easy",
        scenario_metadata=metadata or {
            "topic": "Restaurant conversation",
            "assigned_task": "You are in a cafe. Order your food and keep the conversation polite.",
            "persona": "Polite waiter",
        },
    )


def test_lesson_runtime_generates_package_and_advances():
    scenario = make_scenario()
    package = LessonRuntimeService.create_lesson_package(scenario=scenario, level="beginner")
    state = LessonRuntimeService.initial_state(package)

    assert package.lesson_id
    assert len(package.objectives) == 2
    assert state.last_question == package.objectives[0].main_question

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
    assert "Wrap up the conversation politely" in second_result.assistant_text


def test_lesson_hint_highlights_missing_points():
    scenario = make_scenario(learning_objectives=["ordering food"])
    package = LessonRuntimeService.create_lesson_package(scenario=scenario, level="beginner")
    state = LessonRuntimeService.initial_state(package)

    hint = LessonRuntimeService.build_hint(
        package=package,
        state=state,
        user_last_answer="I want food.",
    )

    assert hint.lesson_id == package.lesson_id
    assert hint.objective_id == package.objectives[0].objective_id
    assert hint.keywords
    assert "Tra loi toi da" in hint.answer_strategy_vi

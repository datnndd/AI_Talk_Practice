from app.modules.scenarios.services.admin_scenario_service import AdminScenarioService


def test_generate_default_prompt_includes_tasks():
    prompt = AdminScenarioService.generate_default_prompt(
        title="Introduce Yourself",
        description="The learner introduces basic personal information.",
        ai_role="Friendly teacher",
        user_role="New learner",
        tasks=["Say your name", "Say your age", "Say where you are from"],
    )

    assert "Say your name" in prompt
    assert "Say your age" in prompt
    assert "Say where you are from" in prompt

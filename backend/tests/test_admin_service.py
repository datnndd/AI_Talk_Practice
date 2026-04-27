import pytest
from app.modules.scenarios.services.admin_scenario_service import AdminScenarioService
from app.modules.scenarios.schemas.admin_scenario import PromptQualityAssessment

def test_assess_prompt_quality_high_quality():
    """Test assess_prompt_quality with a high-quality prompt."""
    prompt = (
        "You are a professional barista. Your role is to help the user practice ordering coffee. "
        "Ask follow-up questions if their order is incomplete. Stay in character and maintain a friendly tone. "
        "Correct the user's pronunciation and offer feedback on their vocabulary. "
        "Avoid using technical jargon unless explained. Do not break character."
    )
    description = "A coffee shop scenario where the user orders a drink."
    tasks = ["Order a coffee", "Ask about the price"]
    
    assessment = AdminScenarioService.assess_prompt_quality(
        prompt=prompt,
        description=description,
        tasks=tasks,
    )
    
    assert isinstance(assessment, PromptQualityAssessment)
    assert assessment.score >= 70
    assert assessment.is_acceptable is True
    assert len(assessment.warnings) == 0

def test_assess_prompt_quality_low_quality():
    """Test assess_prompt_quality with a low-quality prompt."""
    prompt = "Order a coffee."
    description = "Coffee shop."
    tasks = ["Order a coffee"]
    
    assessment = AdminScenarioService.assess_prompt_quality(
        prompt=prompt,
        description=description,
        tasks=tasks,
    )
    
    assert assessment.score < 50
    assert assessment.is_acceptable is False
    assert len(assessment.warnings) > 0
    assert any("too short" in w.lower() for w in assessment.warnings)

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

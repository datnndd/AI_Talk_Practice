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
    target_skills = ["pronunciation", "vocabulary", "small_talk"]
    
    assessment = AdminScenarioService.assess_prompt_quality(
        prompt=prompt,
        description=description,
        target_skills=target_skills
    )
    
    assert isinstance(assessment, PromptQualityAssessment)
    assert assessment.score >= 70
    assert assessment.is_acceptable is True
    assert len(assessment.warnings) == 0

def test_assess_prompt_quality_low_quality():
    """Test assess_prompt_quality with a low-quality prompt."""
    prompt = "Order a coffee."
    description = "Coffee shop."
    target_skills = ["vocabulary"]
    
    assessment = AdminScenarioService.assess_prompt_quality(
        prompt=prompt,
        description=description,
        target_skills=target_skills
    )
    
    assert assessment.score < 50
    assert assessment.is_acceptable is False
    assert len(assessment.warnings) > 0
    assert any("too short" in w.lower() for w in assessment.warnings)

def test_suggest_target_skills_uses_category_and_keywords():
    """Target skill suggestions remain available without variation generation."""

    skills = AdminScenarioService.suggest_target_skills(
        "The learner needs to present clearly and respond with correct grammar.",
        category="interview",
    )

    assert "presentation" in skills
    assert "grammar" in skills
    assert "fluency" in skills

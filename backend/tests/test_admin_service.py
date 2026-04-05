import pytest
from app.services.admin_scenario_service import AdminScenarioService
from app.schemas.admin_scenario import PromptQualityAssessment

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

def test_heuristic_variation_blueprints():
    """Test _heuristic_variation_blueprints generates expected structure."""
    from app.models.scenario import Scenario
    
    scenario = Scenario(
        id=1,
        title="Job Interview",
        description="A formal job interview simulation.",
        category="interview",
        target_skills=["presentation", "grammar"]
    )
    
    count = 3
    blueprints = AdminScenarioService._heuristic_variation_blueprints(scenario, count=count)
    
    assert len(blueprints) == count
    for bp in blueprints:
        assert "variation_name" in bp
        assert "parameters" in bp
        assert "sample_prompt" in bp
        assert "sample_conversation" in bp
        assert len(bp["sample_conversation"]) >= 2
        assert bp["parameters"]["tone"] in ["formal", "friendly", "urgent", "warm", "assertive"]

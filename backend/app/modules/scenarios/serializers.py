from __future__ import annotations

from app.modules.scenarios.models import Scenario, ScenarioPromptHistory
from app.modules.scenarios.schemas import (
    PromptHistoryRead,
    PromptQualityAssessment,
    ScenarioAdminRead,
    ScenarioRead,
)


def serialize_admin_prompt_history(item: ScenarioPromptHistory) -> PromptHistoryRead:
    return PromptHistoryRead.model_validate(item)


def serialize_admin_scenario(
    scenario: Scenario,
    *,
    usage_count: int = 0,
    latest_prompt_quality: PromptQualityAssessment | None = None,
    include_prompt_history: bool = True,
) -> ScenarioAdminRead:
    metadata = scenario.scenario_metadata or {}
    return ScenarioAdminRead.model_validate(
        {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "ai_system_prompt": scenario.ai_system_prompt,
            "ai_role": scenario.ai_role or metadata.get("persona") or metadata.get("partner_persona") or "",
            "user_role": scenario.user_role or metadata.get("learner_role") or "",
            "learning_objectives": scenario.learning_objectives or [],
            "target_skills": scenario.target_skills or [],
            "tags": scenario.tags or [],
            "estimated_duration_minutes": int(scenario.estimated_duration / 60)
            if scenario.estimated_duration
            else None,
            "mode": scenario.mode,
            "metadata": metadata,
            "is_active": scenario.is_active,
            "deleted_at": scenario.deleted_at,
            "created_by": scenario.created_by,
            "usage_count": usage_count,
            "latest_prompt_quality": latest_prompt_quality,
            "prompt_history": [
                serialize_admin_prompt_history(item) for item in getattr(scenario, "prompt_history", [])
            ]
            if include_prompt_history
            else [],
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        }
    )


def serialize_scenario(
    scenario: Scenario,
) -> ScenarioRead:
    metadata = scenario.scenario_metadata or {}
    return ScenarioRead.model_validate(
        {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "learning_objectives": scenario.learning_objectives,
            "ai_system_prompt": scenario.ai_system_prompt,
            "ai_role": scenario.ai_role or metadata.get("persona") or metadata.get("partner_persona") or "",
            "user_role": scenario.user_role or metadata.get("learner_role") or "",
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "target_skills": scenario.target_skills,
            "tags": scenario.tags,
            "estimated_duration": scenario.estimated_duration,
            "mode": scenario.mode,
            "metadata": metadata,
            "is_active": scenario.is_active,
            "created_by": scenario.created_by,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        }
    )

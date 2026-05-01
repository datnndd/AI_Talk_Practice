from __future__ import annotations

from app.modules.characters.serializers import serialize_character
from app.modules.scenarios.models import Scenario
from app.modules.scenarios.schemas import (
    ScenarioAdminRead,
    ScenarioListRead,
    ScenarioRead,
)


def serialize_admin_scenario(
    scenario: Scenario,
    *,
    usage_count: int = 0,
) -> ScenarioAdminRead:
    return ScenarioAdminRead.model_validate(
        {
            "id": scenario.id,
            "character_id": scenario.character_id,
            "title": scenario.title,
            "description": scenario.description,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "ai_system_prompt": scenario.ai_system_prompt,
            "ai_role": scenario.ai_role or "",
            "user_role": scenario.user_role or "",
            "image_url": scenario.image_url,
            "character": serialize_character(scenario.character) if scenario.character else None,
            "tasks": scenario.tasks or [],
            "tags": scenario.tags or [],
            "estimated_duration_minutes": int(scenario.estimated_duration / 60)
            if scenario.estimated_duration
            else None,
            "is_active": scenario.is_active,
            "is_pro": scenario.is_pro,
            "deleted_at": scenario.deleted_at,
            "usage_count": usage_count,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        }
    )


def serialize_scenario(
    scenario: Scenario,
) -> ScenarioRead:
    return ScenarioRead.model_validate(
        {
            "id": scenario.id,
            "character_id": scenario.character_id,
            "title": scenario.title,
            "description": scenario.description,
            "ai_system_prompt": scenario.ai_system_prompt,
            "ai_role": scenario.ai_role or "",
            "user_role": scenario.user_role or "",
            "image_url": scenario.image_url,
            "tasks": scenario.tasks,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "tags": scenario.tags,
            "estimated_duration": scenario.estimated_duration,
            "is_active": scenario.is_active,
            "is_pro": scenario.is_pro,
            "character": serialize_character(scenario.character) if scenario.character else None,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        }
    )


def serialize_scenario_list_item(
    scenario: Scenario,
) -> ScenarioListRead:
    return ScenarioListRead.model_validate(
        {
            "id": scenario.id,
            "character_id": scenario.character_id,
            "title": scenario.title,
            "description": scenario.description,
            "ai_role": scenario.ai_role or "",
            "user_role": scenario.user_role or "",
            "image_url": scenario.image_url,
            "tasks": scenario.tasks,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "tags": scenario.tags,
            "estimated_duration": scenario.estimated_duration,
            "is_active": scenario.is_active,
            "is_pro": scenario.is_pro,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        }
    )

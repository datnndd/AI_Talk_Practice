from __future__ import annotations

from app.modules.scenarios.models import Scenario, ScenarioPromptHistory, ScenarioVariation
from app.modules.scenarios.schemas import (
    PromptHistoryRead,
    PromptQualityAssessment,
    ScenarioAdminRead,
    ScenarioRead,
    ScenarioVariationAdminRead,
    ScenarioVariationRead,
)


def serialize_variation(variation: ScenarioVariation) -> ScenarioVariationRead:
    return ScenarioVariationRead.model_validate(variation)


def serialize_admin_prompt_history(item: ScenarioPromptHistory) -> PromptHistoryRead:
    return PromptHistoryRead.model_validate(item)


def serialize_admin_variation(variation: ScenarioVariation) -> ScenarioVariationAdminRead:
    return ScenarioVariationAdminRead.model_validate(
        {
            "id": variation.id,
            "scenario_id": variation.scenario_id,
            "variation_seed": variation.variation_seed,
            "variation_name": variation.variation_name,
            "parameters": variation.parameters or {},
            "sample_prompt": variation.sample_prompt,
            "sample_conversation": variation.sample_conversation or [],
            "system_prompt_override": variation.system_prompt_override,
            "is_active": variation.is_active,
            "is_pregenerated": variation.is_pregenerated,
            "is_approved": variation.is_approved,
            "generated_by_model": variation.generated_by_model,
            "generation_latency_ms": variation.generation_latency_ms,
            "usage_count": variation.usage_count,
            "last_used_at": variation.last_used_at,
            "created_at": variation.created_at,
            "updated_at": variation.updated_at,
        }
    )


def serialize_admin_scenario(
    scenario: Scenario,
    *,
    usage_count: int = 0,
    latest_prompt_quality: PromptQualityAssessment | None = None,
    include_variations: bool = True,
    include_prompt_history: bool = True,
) -> ScenarioAdminRead:
    variations = getattr(scenario, "variations", []) or []
    active_variation_count = sum(1 for item in variations if item.is_active)
    return ScenarioAdminRead.model_validate(
        {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "opening_message": scenario.opening_message,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "ai_system_prompt": scenario.ai_system_prompt,
            "learning_objectives": scenario.learning_objectives or [],
            "target_skills": scenario.target_skills or [],
            "tags": scenario.tags or [],
            "estimated_duration_minutes": int(scenario.estimated_duration / 60)
            if scenario.estimated_duration
            else None,
            "is_pre_generated": scenario.is_pre_generated,
            "pre_gen_count": scenario.pre_gen_count,
            "mode": scenario.mode,
            "is_ai_start_first": scenario.is_ai_start_first,
            "metadata": scenario.scenario_metadata or {},
            "is_active": scenario.is_active,
            "deleted_at": scenario.deleted_at,
            "created_by": scenario.created_by,
            "usage_count": usage_count,
            "variation_count": len(variations),
            "active_variation_count": active_variation_count,
            "latest_prompt_quality": latest_prompt_quality,
            "variations": [serialize_admin_variation(item) for item in variations] if include_variations else [],
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
    *,
    include_variations: bool = False,
) -> ScenarioRead:
    return ScenarioRead.model_validate(
        {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "learning_objectives": scenario.learning_objectives,
            "ai_system_prompt": scenario.ai_system_prompt,
            "opening_message": scenario.opening_message,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "target_skills": scenario.target_skills,
            "tags": scenario.tags,
            "estimated_duration": scenario.estimated_duration,
            "mode": scenario.mode,
            "is_ai_start_first": scenario.is_ai_start_first,
            "metadata": scenario.scenario_metadata or {},
            "is_active": scenario.is_active,
            "created_by": scenario.created_by,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
            "variations": [serialize_variation(item) for item in getattr(scenario, "variations", [])]
            if include_variations
            else [],
        }
    )

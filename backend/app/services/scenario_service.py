from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictError, NotFoundError
from app.models.scenario import Scenario, ScenarioVariation
from app.repositories.scenario_repository import ScenarioRepository
from app.schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
    ScenarioVariationCreate,
)
from app.services.variation_service import VariationService

logger = logging.getLogger(__name__)


class ScenarioService:
    @staticmethod
    async def list_active(
        db: AsyncSession,
        category: str | None = None,
        difficulty: str | None = None,
    ) -> list[Scenario]:
        return await ScenarioRepository.list_scenarios(
            db,
            category=category,
            difficulty=difficulty,
            is_active=True,
            include_variations=False,
        )

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        scenario_id: int,
        *,
        include_variations: bool = True,
    ) -> Scenario:
        scenario = await ScenarioRepository.get_by_id(
            db,
            scenario_id,
            include_variations=include_variations,
        )
        if scenario is None:
            raise NotFoundError("Scenario not found")
        return scenario

    @staticmethod
    async def create(db: AsyncSession, user_id: int, body: ScenarioCreate) -> Scenario:
        scenario = await ScenarioRepository.create(
            db,
            title=body.title,
            description=body.description,
            learning_objectives=body.learning_objectives,
            ai_system_prompt=body.ai_system_prompt,
            category=body.category,
            difficulty=body.difficulty,
            target_skills=body.target_skills,
            tags=body.tags,
            estimated_duration=body.estimated_duration,
            mode=body.mode,
            scenario_metadata=body.metadata,
            is_active=body.is_active,
            created_by=user_id,
        )
        await db.commit()
        await db.refresh(scenario)
        logger.info("Created scenario id=%s by user id=%s", scenario.id, user_id)
        return await ScenarioService.get_by_id(db, scenario.id, include_variations=True)

    @staticmethod
    async def update(db: AsyncSession, scenario_id: int, body: ScenarioUpdate) -> Scenario:
        scenario = await ScenarioService.get_by_id(db, scenario_id, include_variations=False)
        update_data = body.model_dump(exclude_unset=True)
        if "metadata" in update_data:
            update_data["scenario_metadata"] = update_data.pop("metadata")

        for key, value in update_data.items():
            setattr(scenario, key, value)

        await db.commit()
        await db.refresh(scenario)
        logger.info("Updated scenario id=%s", scenario.id)
        return await ScenarioService.get_by_id(db, scenario.id, include_variations=True)

    @staticmethod
    async def delete(db: AsyncSession, scenario_id: int) -> None:
        scenario = await ScenarioService.get_by_id(db, scenario_id, include_variations=False)
        scenario.is_active = False
        from datetime import datetime, timezone

        scenario.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Soft-deleted scenario id=%s", scenario.id)

    @staticmethod
    async def list_variations(db: AsyncSession, scenario_id: int) -> list[ScenarioVariation]:
        await ScenarioService.get_by_id(db, scenario_id, include_variations=False)
        return await ScenarioRepository.list_variations(db, scenario_id)

    @staticmethod
    async def create_variation(
        db: AsyncSession,
        scenario_id: int,
        body: ScenarioVariationCreate,
    ) -> ScenarioVariation:
        scenario = await ScenarioService.get_by_id(db, scenario_id, include_variations=False)
        variation_seed = body.variation_seed or VariationService.build_variation_seed(
            scenario_id=scenario.id,
            parameters=body.parameters,
            mode=scenario.mode,
        )
        existing = await ScenarioRepository.get_variation_by_seed(
            db,
            scenario_id=scenario.id,
            variation_seed=variation_seed,
        )
        if existing is not None:
            raise ConflictError(
                "Scenario variation already exists",
                extra={"variation_id": existing.id, "variation_seed": existing.variation_seed},
            )

        variation = await ScenarioRepository.create_variation(
            db,
            scenario_id=scenario.id,
            variation_seed=variation_seed,
            parameters=body.parameters,
            system_prompt_override=body.system_prompt_override,
            sample_prompt=body.sample_prompt,
            is_pregenerated=body.is_pregenerated,
            generated_by_model=body.generated_by_model,
            generation_latency_ms=body.generation_latency_ms,
            is_approved=body.is_approved,
        )
        await db.commit()
        await db.refresh(variation)
        logger.info("Created scenario variation id=%s for scenario id=%s", variation.id, scenario.id)
        return variation

from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.scenarios.models.scenario import Scenario
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.scenarios.schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
)

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
        )

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        scenario_id: int,
    ) -> Scenario:
        scenario = await ScenarioRepository.get_by_id(
            db,
            scenario_id,
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
            ai_role=body.ai_role,
            user_role=body.user_role,
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
        return await ScenarioService.get_by_id(db, scenario.id)

    @staticmethod
    async def update(db: AsyncSession, scenario_id: int, body: ScenarioUpdate) -> Scenario:
        scenario = await ScenarioService.get_by_id(db, scenario_id)
        update_data = body.model_dump(exclude_unset=True)
        if "metadata" in update_data:
            update_data["scenario_metadata"] = update_data.pop("metadata")
        if "ai_role" in update_data and update_data["ai_role"] is not None:
            update_data["ai_role"] = update_data["ai_role"].strip()
        if "user_role" in update_data and update_data["user_role"] is not None:
            update_data["user_role"] = update_data["user_role"].strip()

        for key, value in update_data.items():
            setattr(scenario, key, value)

        await db.commit()
        await db.refresh(scenario)
        logger.info("Updated scenario id=%s", scenario.id)
        return await ScenarioService.get_by_id(db, scenario.id)

    @staticmethod
    async def delete(db: AsyncSession, scenario_id: int) -> None:
        scenario = await ScenarioService.get_by_id(db, scenario_id)
        scenario.is_active = False
        from datetime import datetime, timezone

        scenario.deleted_at = datetime.now(timezone.utc)
        await db.commit()
        logger.info("Soft-deleted scenario id=%s", scenario.id)

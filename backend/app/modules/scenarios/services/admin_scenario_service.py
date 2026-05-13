from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.characters.services import CharacterService
from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.models.session import Session
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.scenarios.schemas.admin_scenario import (
    BulkScenarioActionRequest,
    ScenarioAdminCreate,
    ScenarioAdminUpdate,
)

logger = logging.getLogger(__name__)

class AdminScenarioService:
    @staticmethod
    async def _scenario_usage_counts(db: AsyncSession, scenario_ids: list[int]) -> dict[int, int]:
        if not scenario_ids:
            return {}
        stmt = (
            select(Session.scenario_id, func.count(Session.id))
            .where(Session.scenario_id.in_(scenario_ids), Session.deleted_at.is_(None))
            .group_by(Session.scenario_id)
        )
        rows = (await db.execute(stmt)).all()
        return {scenario_id: int(count) for scenario_id, count in rows}

    @classmethod
    async def get_scenario_usage_count(cls, db: AsyncSession, scenario_id: int) -> int:
        return (await cls._scenario_usage_counts(db, [scenario_id])).get(scenario_id, 0)

    @classmethod
    async def list_scenarios(
        cls,
        db: AsyncSession,
        *,
        search: str | None,
        category: str | None,
        difficulty: str | None,
        tag: str | None,
        include_deleted: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Scenario], dict[int, int], int]:
        scenarios, total = await ScenarioRepository.list_admin_scenarios(
            db,
            search=search,
            category=category,
            difficulty=difficulty,
            tag=tag,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )
        usage_counts = await cls._scenario_usage_counts(db, [scenario.id for scenario in scenarios])
        return scenarios, usage_counts, total

    @staticmethod
    async def get_scenario(db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await ScenarioRepository.get_admin_scenario_by_id(db, scenario_id, include_deleted=True)
        if scenario is None:
            raise NotFoundError("Scenario not found")
        return scenario

    @classmethod
    async def create_scenario(
        cls,
        db: AsyncSession,
        *,
        user_id: int,
        body: ScenarioAdminCreate,
    ) -> Scenario:
        await CharacterService.ensure_active_character(db, body.character_id)

        scenario = await ScenarioRepository.create(
            db,
            title=body.title,
            description=body.description,
            ai_role=body.ai_role.strip(),
            user_role=body.user_role.strip(),
            tasks=body.tasks,
            category=body.category,
            difficulty=body.difficulty,
            tags=body.tags,
            time_limit_minutes=body.time_limit_minutes or 10,
            character_id=body.character_id,
            is_active=body.is_active,
            is_pro=body.is_pro,
            image_url=body.image_url,
        )
        await db.commit()
        return await cls.get_scenario(db, scenario.id)

    @classmethod
    async def update_scenario(
        cls,
        db: AsyncSession,
        *,
        scenario_id: int,
        user_id: int,
        body: ScenarioAdminUpdate,
    ) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        update_data = body.model_dump(exclude_unset=True)

        if "ai_role" in update_data and update_data["ai_role"] is not None:
            update_data["ai_role"] = update_data["ai_role"].strip()
        if "user_role" in update_data and update_data["user_role"] is not None:
            update_data["user_role"] = update_data["user_role"].strip()
        if "time_limit_minutes" in update_data:
            update_data["time_limit_minutes"] = update_data["time_limit_minutes"] or None
        if "character_id" in update_data:
            await CharacterService.ensure_active_character(db, update_data["character_id"])

        for key, value in update_data.items():
            setattr(scenario, key, value)

        await db.commit()
        return await cls.get_scenario(db, scenario.id)

    @classmethod
    async def soft_delete_scenario(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.deleted_at = datetime.now(timezone.utc)
        scenario.is_active = False
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @classmethod
    async def restore_scenario(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.deleted_at = None
        scenario.is_active = True
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @classmethod
    async def toggle_scenario_active(cls, db: AsyncSession, scenario_id: int) -> Scenario:
        scenario = await cls.get_scenario(db, scenario_id)
        scenario.is_active = not scenario.is_active
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @classmethod
    async def bulk_action(
        cls,
        *,
        db: AsyncSession,
        user_id: int,
        body: BulkScenarioActionRequest,
    ) -> None:
        scenarios = [
            scenario
            for scenario_id in body.scenario_ids
            if (scenario := await ScenarioRepository.get_admin_scenario_by_id(db, scenario_id, include_deleted=True))
            is not None
        ]
        if not scenarios:
            raise NotFoundError("No matching scenarios found")

        for scenario in scenarios:
            if body.action == "activate":
                scenario.is_active = True
            elif body.action == "deactivate":
                scenario.is_active = False
            elif body.action == "soft_delete":
                scenario.deleted_at = datetime.now(timezone.utc)
                scenario.is_active = False
        await db.commit()
        return None

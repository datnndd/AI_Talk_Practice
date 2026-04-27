from __future__ import annotations

import logging

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.scenarios.models.scenario import Scenario
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.scenarios.schemas.scenario import (
    ScenarioCreate,
    ScenarioUpdate,
)
from app.modules.users.models.user import User

logger = logging.getLogger(__name__)


VIP_TIERS = {"PRO", "ENTERPRISE"}


def user_is_vip(user: User | None) -> bool:
    if user is None:
        return False
    subscription = getattr(user, "subscription", None)
    if subscription is None:
        return False
    tier = str(subscription.tier or "").upper()
    status = str(subscription.status or "").lower()
    if tier not in VIP_TIERS or status != "active":
        return False
    if subscription.expires_at is None:
        return True
    from datetime import datetime, timezone

    expires_at = subscription.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    return expires_at > datetime.now(timezone.utc)


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
        user: User | None = None,
        enforce_access: bool = False,
    ) -> Scenario:
        scenario = await ScenarioRepository.get_by_id(
            db,
            scenario_id,
        )
        if scenario is None:
            raise NotFoundError("Scenario not found")
        if enforce_access and scenario.is_pro and not user_is_vip(user):
            raise ForbiddenError("This scenario requires VIP access")
        return scenario

    @staticmethod
    async def create(db: AsyncSession, user_id: int, body: ScenarioCreate) -> Scenario:
        scenario = await ScenarioRepository.create(
            db,
            title=body.title,
            description=body.description,
            ai_system_prompt=body.ai_system_prompt,
            ai_role=body.ai_role,
            user_role=body.user_role,
            tasks=body.tasks,
            category=body.category,
            difficulty=body.difficulty,
            tags=body.tags,
            estimated_duration=body.estimated_duration,
            is_active=body.is_active,
            is_pro=body.is_pro,
        )
        await db.commit()
        await db.refresh(scenario)
        logger.info("Created scenario id=%s by user id=%s", scenario.id, user_id)
        return await ScenarioService.get_by_id(db, scenario.id)

    @staticmethod
    async def update(db: AsyncSession, scenario_id: int, body: ScenarioUpdate) -> Scenario:
        scenario = await ScenarioService.get_by_id(db, scenario_id)
        update_data = body.model_dump(exclude_unset=True)
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

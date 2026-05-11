from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.scenarios.models.scenario import Scenario
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.users.models.user import User


VIP_TIERS = {"PRO"}


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


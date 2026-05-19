from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError, NotFoundError
from app.modules.scenarios.models.scenario import Scenario
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.sessions.repository import SessionRepository
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

    @staticmethod
    async def get_objective_completion_progress(
        db: AsyncSession,
        *,
        scenario_id: int,
        user_id: int,
    ) -> dict:
        session = await SessionRepository.get_latest_objective_completed_for_user_scenario(
            db,
            user_id=user_id,
            scenario_id=scenario_id,
        )
        if session is None:
            return {
                "has_completed_session": False,
                "latest_completed_session_id": None,
                "latest_completed_session_result_url": None,
                "objective_completion": None,
            }
        metadata = dict(session.score.score_metadata or {}) if session.score else {}
        objective_completion = metadata.get("objective_completion")
        return {
            "has_completed_session": True,
            "latest_completed_session_id": session.id,
            "latest_completed_session_result_url": f"/sessions/{session.id}/result",
            "objective_completion": objective_completion,
        }

    @staticmethod
    async def get_objective_completion_progress_by_scenario(
        db: AsyncSession,
        *,
        scenario_ids: list[int],
        user_id: int,
    ) -> dict[int, dict]:
        sessions = await SessionRepository.get_latest_objective_completed_by_scenario_for_user(
            db,
            user_id=user_id,
            scenario_ids=scenario_ids,
        )
        progress_by_scenario: dict[int, dict] = {}
        for scenario_id in scenario_ids:
            session = sessions.get(scenario_id)
            if session is None:
                progress_by_scenario[scenario_id] = {
                    "has_completed_session": False,
                    "latest_completed_session_id": None,
                    "latest_completed_session_result_url": None,
                    "objective_completion": None,
                }
                continue
            metadata = dict(session.score.score_metadata or {}) if session.score else {}
            objective_completion = metadata.get("objective_completion")
            progress_by_scenario[scenario_id] = {
                "has_completed_session": True,
                "latest_completed_session_id": session.id,
                "latest_completed_session_result_url": f"/sessions/{session.id}/result",
                "objective_completion": objective_completion,
            }
        return progress_by_scenario


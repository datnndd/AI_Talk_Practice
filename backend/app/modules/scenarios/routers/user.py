"""Scenario endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.users.models.user import User
from app.modules.scenarios.schemas import ScenarioListRead, ScenarioRead
from app.modules.scenarios.serializers import serialize_scenario, serialize_scenario_list_item
from app.modules.scenarios.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioListRead])
async def list_scenarios(
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scenarios = await ScenarioService.list_active(db, category, difficulty)
    progress_by_scenario = await ScenarioService.get_objective_completion_progress_by_scenario(
        db,
        scenario_ids=[scenario.id for scenario in scenarios],
        user_id=user.id,
    )
    return [
        serialize_scenario_list_item(item, progress=progress_by_scenario.get(item.id))
        for item in scenarios
    ]


@router.get("/{scenario_id}", response_model=ScenarioRead)
async def get_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scenario = await ScenarioService.get_by_id(db, scenario_id, user=user, enforce_access=True)
    progress = await ScenarioService.get_objective_completion_progress(
        db,
        scenario_id=scenario.id,
        user_id=user.id,
    )
    return serialize_scenario(scenario, progress=progress)

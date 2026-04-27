"""Scenario endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.users.models.user import User
from app.modules.scenarios.schemas import (
    ScenarioCreate,
    ScenarioRead,
    ScenarioUpdate,
)
from app.modules.scenarios.serializers import serialize_scenario
from app.modules.scenarios.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioRead])
async def list_scenarios(
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    scenarios = await ScenarioService.list_active(db, category, difficulty)
    return [serialize_scenario(item) for item in scenarios]


@router.get("/{scenario_id}", response_model=ScenarioRead)
async def get_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scenario = await ScenarioService.get_by_id(db, scenario_id, user=user, enforce_access=True)
    return serialize_scenario(scenario)


@router.post("", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    body: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scenario = await ScenarioService.create(db, user.id, body)
    return serialize_scenario(scenario)


@router.put("/{scenario_id}", response_model=ScenarioRead)
async def update_scenario(
    scenario_id: int,
    body: ScenarioUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scenario = await ScenarioService.update(db, scenario_id, body)
    return serialize_scenario(scenario)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await ScenarioService.delete(db, scenario_id)

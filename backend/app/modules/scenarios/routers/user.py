"""Scenario and scenario variation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.users.models.user import User
from app.modules.scenarios.schemas import (
    ScenarioCreate,
    ScenarioRead,
    ScenarioUpdate,
    ScenarioVariationCreate,
    ScenarioVariationRead,
)
from app.modules.scenarios.serializers import serialize_scenario, serialize_variation
from app.modules.scenarios.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioRead])
async def list_scenarios(
    category: str | None = Query(default=None),
    difficulty: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
):
    scenarios = await ScenarioService.list_active(db, category, difficulty)
    return [serialize_scenario(item, include_variations=False) for item in scenarios]


@router.get("/{scenario_id}", response_model=ScenarioRead)
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    scenario = await ScenarioService.get_by_id(db, scenario_id, include_variations=True)
    return serialize_scenario(scenario, include_variations=True)


@router.post("", response_model=ScenarioRead, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    body: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scenario = await ScenarioService.create(db, user.id, body)
    return serialize_scenario(scenario, include_variations=True)


@router.put("/{scenario_id}", response_model=ScenarioRead)
async def update_scenario(
    scenario_id: int,
    body: ScenarioUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    scenario = await ScenarioService.update(db, scenario_id, body)
    return serialize_scenario(scenario, include_variations=True)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    await ScenarioService.delete(db, scenario_id)


@router.get("/{scenario_id}/variations", response_model=list[ScenarioVariationRead])
async def list_variations(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
):
    variations = await ScenarioService.list_variations(db, scenario_id)
    return [serialize_variation(item) for item in variations]


@router.post(
    "/{scenario_id}/variations",
    response_model=ScenarioVariationRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_variation(
    scenario_id: int,
    body: ScenarioVariationCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    variation = await ScenarioService.create_variation(db, scenario_id, body)
    return serialize_variation(variation)

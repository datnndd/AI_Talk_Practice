"""
Scenario CRUD router.
"""

from typing import List

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate, ScenarioResponse
from app.services.scenario_service import ScenarioService

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios(
    category: str | None = Query(None),
    difficulty: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    scenarios = await ScenarioService.list_active(db, category, difficulty)
    return scenarios

@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    scenario = await ScenarioService.get_by_id(db, scenario_id)
    return scenario

@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    body: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scenario = await ScenarioService.create(db, user.id, body)
    return scenario

@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: int,
    body: ScenarioUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user), # Requires auth
):
    scenario = await ScenarioService.update(db, scenario_id, body)
    return scenario

@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user), # Requires auth
):
    await ScenarioService.delete(db, scenario_id)

"""
Scenario CRUD router.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.schemas import ScenarioCreate, ScenarioUpdate, ScenarioResponse
from app.models.scenario import Scenario
from app.models.user import User

router = APIRouter(prefix="/api/scenarios", tags=["scenarios"])


@router.get("", response_model=List[ScenarioResponse])
async def list_scenarios(
    category: str | None = Query(None),
    difficulty: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List active scenarios, optionally filtered by category/difficulty."""
    q = select(Scenario).where(Scenario.is_active == True)
    if category:
        q = q.where(Scenario.category == category)
    if difficulty:
        q = q.where(Scenario.difficulty == difficulty)
    q = q.order_by(Scenario.id)
    result = await db.execute(q)
    return result.scalars().all()


@router.get("/{scenario_id}", response_model=ScenarioResponse)
async def get_scenario(scenario_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario


@router.post("", response_model=ScenarioResponse, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    body: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    scenario = Scenario(
        title=body.title,
        description=body.description,
        learning_objectives=body.learning_objectives,
        ai_system_prompt=body.ai_system_prompt,
        category=body.category,
        difficulty=body.difficulty,
        created_by=user.id,
    )
    db.add(scenario)
    await db.commit()
    await db.refresh(scenario)
    return scenario


@router.put("/{scenario_id}", response_model=ScenarioResponse)
async def update_scenario(
    scenario_id: int,
    body: ScenarioUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    update_data = body.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(scenario, key, value)

    await db.commit()
    await db.refresh(scenario)
    return scenario


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
    scenario = result.scalar_one_or_none()
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    await db.delete(scenario)
    await db.commit()

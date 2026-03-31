from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.scenario import Scenario
from app.schemas.scenario import ScenarioCreate, ScenarioUpdate

class ScenarioService:
    @staticmethod
    async def list_active(db: AsyncSession, category: str | None = None, difficulty: str | None = None) -> List[Scenario]:
        q = select(Scenario).where(Scenario.is_active == True)
        if category:
            q = q.where(Scenario.category == category)
        if difficulty:
            q = q.where(Scenario.difficulty == difficulty)
        q = q.order_by(Scenario.id)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, scenario_id: int) -> Scenario:
        result = await db.execute(select(Scenario).where(Scenario.id == scenario_id))
        scenario = result.scalar_one_or_none()
        if not scenario:
            raise HTTPException(status_code=404, detail="Scenario not found")
        return scenario

    @staticmethod
    async def create(db: AsyncSession, user_id: int, body: ScenarioCreate) -> Scenario:
        scenario = Scenario(
            title=body.title,
            description=body.description,
            learning_objectives=body.learning_objectives,
            ai_system_prompt=body.ai_system_prompt,
            category=body.category,
            difficulty=body.difficulty,
            created_by=user_id,
        )
        db.add(scenario)
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @staticmethod
    async def update(db: AsyncSession, scenario_id: int, body: ScenarioUpdate) -> Scenario:
        scenario = await ScenarioService.get_by_id(db, scenario_id)
        update_data = body.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(scenario, key, value)
        await db.commit()
        await db.refresh(scenario)
        return scenario

    @staticmethod
    async def delete(db: AsyncSession, scenario_id: int) -> None:
        scenario = await ScenarioService.get_by_id(db, scenario_id)
        await db.delete(scenario)
        await db.commit()

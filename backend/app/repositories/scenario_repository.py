from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.scenario import Scenario, ScenarioVariation


class ScenarioRepository:
    @staticmethod
    def _scenario_query(*, include_deleted: bool = False) -> Select[tuple[Scenario]]:
        stmt = select(Scenario)
        if not include_deleted:
            stmt = stmt.where(Scenario.deleted_at.is_(None))
        return stmt

    @classmethod
    async def list_scenarios(
        cls,
        db: AsyncSession,
        *,
        category: str | None = None,
        difficulty: str | None = None,
        is_active: bool | None = True,
        include_variations: bool = False,
    ) -> list[Scenario]:
        stmt = cls._scenario_query()
        if include_variations:
            stmt = stmt.options(selectinload(Scenario.variations))
        if is_active is not None:
            stmt = stmt.where(Scenario.is_active.is_(is_active))
        if category:
            stmt = stmt.where(Scenario.category == category)
        if difficulty:
            stmt = stmt.where(Scenario.difficulty == difficulty)
        stmt = stmt.order_by(Scenario.id.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        scenario_id: int,
        *,
        include_deleted: bool = False,
        include_variations: bool = False,
    ) -> Scenario | None:
        stmt = cls._scenario_query(include_deleted=include_deleted).where(Scenario.id == scenario_id)
        if include_variations:
            stmt = stmt.options(selectinload(Scenario.variations))
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, **values: object) -> Scenario:
        scenario = Scenario(**values)
        db.add(scenario)
        await db.flush()
        return scenario

    @staticmethod
    async def get_variation_by_id(
        db: AsyncSession,
        variation_id: int,
        *,
        scenario_id: int | None = None,
    ) -> ScenarioVariation | None:
        stmt = select(ScenarioVariation).where(ScenarioVariation.id == variation_id)
        if scenario_id is not None:
            stmt = stmt.where(ScenarioVariation.scenario_id == scenario_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_variation_by_seed(
        db: AsyncSession,
        *,
        scenario_id: int,
        variation_seed: str,
    ) -> ScenarioVariation | None:
        stmt = select(ScenarioVariation).where(
            ScenarioVariation.scenario_id == scenario_id,
            ScenarioVariation.variation_seed == variation_seed,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_variations(db: AsyncSession, scenario_id: int) -> list[ScenarioVariation]:
        stmt = (
            select(ScenarioVariation)
            .where(ScenarioVariation.scenario_id == scenario_id)
            .order_by(
                ScenarioVariation.is_pregenerated.desc(),
                ScenarioVariation.is_approved.desc(),
                ScenarioVariation.usage_count.asc(),
                ScenarioVariation.id.asc(),
            )
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def pick_pregenerated_variation(
        db: AsyncSession,
        scenario_id: int,
    ) -> ScenarioVariation | None:
        stmt = (
            select(ScenarioVariation)
            .where(
                ScenarioVariation.scenario_id == scenario_id,
                ScenarioVariation.is_pregenerated.is_(True),
                ScenarioVariation.is_approved.is_(True),
            )
            .order_by(
                ScenarioVariation.usage_count.asc(),
                ScenarioVariation.last_used_at.asc(),
                ScenarioVariation.id.asc(),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_variation(db: AsyncSession, **values: object) -> ScenarioVariation:
        variation = ScenarioVariation(**values)
        db.add(variation)
        await db.flush()
        return variation

    @staticmethod
    async def touch_variation_usage(variation: ScenarioVariation) -> None:
        variation.usage_count = int(variation.usage_count or 0) + 1
        variation.last_used_at = datetime.now(timezone.utc)

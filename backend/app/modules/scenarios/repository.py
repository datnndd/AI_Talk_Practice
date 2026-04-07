from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Select, String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.scenarios.models.scenario import Scenario, ScenarioPromptHistory, ScenarioVariation
from app.modules.sessions.models.session import Session


class ScenarioRepository:
    @staticmethod
    def _truthy(column):
        return or_(
            column.is_(True),
            func.lower(cast(column, String)).in_(("true", "1", "t", "yes", "y", "on")),
        )

    @staticmethod
    def _falsy(column):
        return or_(
            column.is_(False),
            func.lower(cast(column, String)).in_(("false", "0", "f", "no", "n", "off")),
        )

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
            stmt = stmt.where(cls._truthy(Scenario.is_active) if is_active else cls._falsy(Scenario.is_active))
        if category:
            stmt = stmt.where(Scenario.category == category)
        if difficulty:
            stmt = stmt.where(Scenario.difficulty == difficulty)
        stmt = stmt.order_by(Scenario.id.asc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @classmethod
    async def list_admin_scenarios(
        cls,
        db: AsyncSession,
        *,
        search: str | None = None,
        category: str | None = None,
        difficulty: str | None = None,
        tag: str | None = None,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Scenario], int]:
        session_counts = (
            select(
                Session.scenario_id.label("scenario_id"),
                func.count(Session.id).label("usage_count"),
            )
            .where(Session.deleted_at.is_(None))
            .group_by(Session.scenario_id)
            .subquery()
        )

        stmt = (
            cls._scenario_query(include_deleted=include_deleted)
            .outerjoin(session_counts, session_counts.c.scenario_id == Scenario.id)
            .options(
                selectinload(Scenario.variations),
                selectinload(Scenario.prompt_history),
            )
            .order_by(
                func.coalesce(session_counts.c.usage_count, 0).desc(),
                Scenario.updated_at.desc(),
                Scenario.id.desc(),
            )
        )

        count_stmt = select(func.count(Scenario.id))
        if not include_deleted:
            count_stmt = count_stmt.where(Scenario.deleted_at.is_(None))

        filters = []
        if search:
            token = f"%{search.lower()}%"
            filters.append(
                or_(
                    func.lower(Scenario.title).like(token),
                    func.lower(Scenario.description).like(token),
                    func.lower(Scenario.category).like(token),
                    cast(Scenario.tags, String).like(token),
                )
            )
        if category:
            filters.append(Scenario.category == category)
        if difficulty:
            filters.append(Scenario.difficulty == difficulty)
        if tag:
            filters.append(cast(Scenario.tags, String).like(f"%{tag}%"))

        for predicate in filters:
            stmt = stmt.where(predicate)
            count_stmt = count_stmt.where(predicate)

        stmt = stmt.offset(max(page - 1, 0) * page_size).limit(page_size)
        total = int((await db.execute(count_stmt)).scalar_one())
        scenarios = list((await db.execute(stmt)).scalars().unique().all())
        return scenarios, total

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

    @classmethod
    async def get_admin_scenario_by_id(
        cls,
        db: AsyncSession,
        scenario_id: int,
        *,
        include_deleted: bool = True,
    ) -> Scenario | None:
        stmt = (
            cls._scenario_query(include_deleted=include_deleted)
            .where(Scenario.id == scenario_id)
            .options(
                selectinload(Scenario.variations),
                selectinload(Scenario.prompt_history),
            )
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, **values: object) -> Scenario:
        scenario = Scenario(**values)
        db.add(scenario)
        await db.flush()
        return scenario

    @staticmethod
    async def create_prompt_history(db: AsyncSession, **values: object) -> ScenarioPromptHistory:
        history = ScenarioPromptHistory(**values)
        db.add(history)
        await db.flush()
        return history

    @staticmethod
    async def list_prompt_history(db: AsyncSession, scenario_id: int) -> list[ScenarioPromptHistory]:
        stmt = (
            select(ScenarioPromptHistory)
            .where(ScenarioPromptHistory.scenario_id == scenario_id)
            .order_by(ScenarioPromptHistory.created_at.desc(), ScenarioPromptHistory.id.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

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
    async def list_admin_variations(
        db: AsyncSession,
        *,
        scenario_id: int,
        search: str | None = None,
        include_inactive: bool = True,
    ) -> list[ScenarioVariation]:
        stmt = select(ScenarioVariation).where(ScenarioVariation.scenario_id == scenario_id)
        if not include_inactive:
            stmt = stmt.where(ScenarioRepository._truthy(ScenarioVariation.is_active))
        if search:
            token = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(ScenarioVariation.variation_name).like(token),
                    func.lower(func.coalesce(ScenarioVariation.sample_prompt, "")).like(token),
                    cast(ScenarioVariation.parameters, String).like(token),
                )
            )
        stmt = stmt.order_by(
            ScenarioVariation.is_active.desc(),
            ScenarioVariation.is_pregenerated.desc(),
            ScenarioVariation.usage_count.desc(),
            ScenarioVariation.updated_at.desc(),
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
                ScenarioRepository._truthy(ScenarioVariation.is_pregenerated),
                ScenarioRepository._truthy(ScenarioVariation.is_approved),
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

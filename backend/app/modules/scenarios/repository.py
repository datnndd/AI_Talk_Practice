from __future__ import annotations

from sqlalchemy import Select, String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.modules.scenarios.models.scenario import Scenario
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
    def _scenario_query(*, include_deleted: bool = False, include_character: bool = True) -> Select[tuple[Scenario]]:
        stmt = select(Scenario)
        if include_character:
            stmt = stmt.options(joinedload(Scenario.character))
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
    ) -> list[Scenario]:
        stmt = cls._scenario_query(include_character=False)
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
    ) -> Scenario | None:
        stmt = cls._scenario_query(include_deleted=include_deleted).where(Scenario.id == scenario_id)
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
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, **values: object) -> Scenario:
        scenario = Scenario(**values)
        db.add(scenario)
        await db.flush()
        return scenario

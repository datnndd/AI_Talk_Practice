from __future__ import annotations

from sqlalchemy import Select, String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.characters.models import Character


class CharacterRepository:
    @staticmethod
    def _character_query(*, include_deleted: bool = False) -> Select[tuple[Character]]:
        stmt = select(Character)
        if not include_deleted:
            stmt = stmt.where(Character.deleted_at.is_(None))
        return stmt

    @staticmethod
    def _truthy(column):
        return or_(
            column.is_(True),
            func.lower(cast(column, String)).in_(("true", "1", "t", "yes", "y", "on")),
        )

    @classmethod
    async def list_characters(
        cls,
        db: AsyncSession,
        *,
        search: str | None = None,
        active_only: bool = False,
        include_deleted: bool = False,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Character], int]:
        stmt = cls._character_query(include_deleted=include_deleted)
        count_stmt = select(func.count(Character.id))
        if not include_deleted:
            count_stmt = count_stmt.where(Character.deleted_at.is_(None))
        if active_only:
            stmt = stmt.where(cls._truthy(Character.is_active))
            count_stmt = count_stmt.where(cls._truthy(Character.is_active))
        if search:
            token = f"%{search.lower()}%"
            predicate = or_(
                func.lower(Character.name).like(token),
                func.lower(func.coalesce(Character.description, "")).like(token),
                func.lower(Character.tts_voice).like(token),
            )
            stmt = stmt.where(predicate)
            count_stmt = count_stmt.where(predicate)

        stmt = stmt.order_by(Character.sort_order.asc(), Character.id.asc())
        stmt = stmt.offset(max(page - 1, 0) * page_size).limit(page_size)
        total = int((await db.execute(count_stmt)).scalar_one())
        characters = list((await db.execute(stmt)).scalars().all())
        return characters, total

    @classmethod
    async def get_by_id(
        cls,
        db: AsyncSession,
        character_id: int,
        *,
        include_deleted: bool = False,
    ) -> Character | None:
        stmt = cls._character_query(include_deleted=include_deleted).where(Character.id == character_id)
        return (await db.execute(stmt)).scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, **values: object) -> Character:
        character = Character(**values)
        db.add(character)
        await db.flush()
        return character

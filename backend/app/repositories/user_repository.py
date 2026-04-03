from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    @staticmethod
    def _active_query() -> Select[tuple[User]]:
        return select(User).where(User.deleted_at.is_(None))

    @classmethod
    async def get_active_by_id(cls, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(cls._active_query().where(User.id == user_id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_active_by_email(cls, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(cls._active_query().where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(db: AsyncSession, **values: object) -> User:
        user = User(**values)
        db.add(user)
        await db.flush()
        return user

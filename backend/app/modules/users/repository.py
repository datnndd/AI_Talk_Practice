from __future__ import annotations

from sqlalchemy import Select, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User


class UserRepository:
    @staticmethod
    def _active_query() -> Select[tuple[User]]:
        return select(User).where(User.deleted_at.is_(None))

    @classmethod
    async def get_active_by_id(cls, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(cls._active_query().where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    def _admin_query() -> Select[tuple[User]]:
        return select(User).options(
            selectinload(User.subscription),
            selectinload(User.daily_checkins),
            selectinload(User.daily_stats),
        )

    @classmethod
    async def get_by_id(cls, db: AsyncSession, user_id: int) -> User | None:
        result = await db.execute(cls._admin_query().where(User.id == user_id))
        return result.scalar_one_or_none()

    @classmethod
    async def get_active_by_email(cls, db: AsyncSession, email: str) -> User | None:
        result = await db.execute(cls._active_query().where(User.email == email))
        return result.scalar_one_or_none()

    @classmethod
    async def get_active_by_google_id(cls, db: AsyncSession, google_id: str) -> User | None:
        result = await db.execute(cls._active_query().where(User.google_id == google_id))
        return result.scalar_one_or_none()

    @classmethod
    async def list_for_admin(
        cls,
        db: AsyncSession,
        *,
        search: str | None = None,
        status: str | None = None,
        subscription_tier: str | None = None,
    ) -> list[User]:
        stmt = cls._admin_query()

        if search:
            raw_search = search.strip()
            search_term = f"%{raw_search}%"
            search_filters = [
                User.email.ilike(search_term),
                User.display_name.ilike(search_term),
            ]
            if raw_search.isdigit():
                search_filters.append(User.id == int(raw_search))
            stmt = stmt.where(or_(*search_filters))

        normalized_status = (status or "").strip().lower()
        if normalized_status == "active":
            stmt = stmt.where(User.deleted_at.is_(None))
        elif normalized_status == "inactive":
            stmt = stmt.where(User.deleted_at.is_not(None))

        if subscription_tier:
            stmt = (
                stmt.join(Subscription, Subscription.user_id == User.id, isouter=True)
                .where(Subscription.tier == subscription_tier.strip().upper())
            )

        result = await db.execute(stmt.order_by(User.created_at.desc()))
        return list(result.scalars().unique().all())

    @staticmethod
    async def create(db: AsyncSession, **values: object) -> User:
        user = User(**values)
        db.add(user)
        await db.flush()
        return user

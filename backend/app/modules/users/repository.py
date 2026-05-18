from __future__ import annotations

from sqlalchemy import Select, func, not_, or_, select
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
            selectinload(User.daily_stats),
        )

    @staticmethod
    def _admin_role_clause():
        return or_(
            User.role == "admin",
            User.preferences["is_admin"].as_boolean().is_(True),
            User.preferences["role"].as_string() == "admin",
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
        role: str | None = None,
        subscription_tier: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        stmt = select(User)

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

        normalized_role = (role or "").strip().lower()
        if normalized_role in {"admin", "learner"}:
            admin_clause = cls._admin_role_clause()
            stmt = stmt.where(admin_clause if normalized_role == "admin" else not_(admin_clause))

        count_stmt = select(func.count()).select_from(stmt.order_by(None).options().subquery())
        total = int((await db.execute(count_stmt)).scalar_one() or 0)
        offset = (page - 1) * page_size
        result = await db.execute(
            stmt.options(selectinload(User.subscription))
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        return list(result.scalars().unique().all()), total

    @staticmethod
    async def create(db: AsyncSession, **values: object) -> User:
        user = User(**values)
        db.add(user)
        await db.flush()
        return user

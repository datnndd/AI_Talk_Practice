from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User
from app.modules.users.repository import UserRepository
from app.modules.users.schemas.admin_user import (
    AdminUserSubscriptionUpdateRequest,
    AdminUserUpdateRequest,
)
from app.modules.users.serializers import user_is_admin

logger = logging.getLogger(__name__)

PLAN_FEATURES = {
    "FREE": {},
    "PRO": {
        "live_ai_practice": True,
        "advanced_scenarios": True,
        "premium_tutor": True,
    },
    "ENTERPRISE": {
        "live_ai_practice": True,
        "advanced_scenarios": True,
        "premium_tutor": True,
        "enterprise_support": True,
    },
}


class AdminUserService:
    @staticmethod
    async def list_users(
        db: AsyncSession,
        *,
        search: str | None = None,
        status: str | None = None,
        role: str | None = None,
        subscription_tier: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[User], int]:
        users = await UserRepository.list_for_admin(
            db,
            search=search,
            status=status,
            subscription_tier=subscription_tier,
        )
        filtered_users = AdminUserService._apply_role_filter(users, role)
        total = len(filtered_users)
        offset = (page - 1) * page_size
        return filtered_users[offset : offset + page_size], total

    @staticmethod
    async def get_user(db: AsyncSession, user_id: int) -> User:
        user = await UserRepository.get_by_id(db, user_id)
        if user is None:
            raise NotFoundError("User not found")
        return user

    @staticmethod
    async def update_user(
        db: AsyncSession,
        *,
        actor: User,
        user_id: int,
        body: AdminUserUpdateRequest,
    ) -> User:
        user = await AdminUserService.get_user(db, user_id)
        update_data = body.model_dump(exclude_unset=True, exclude={"is_admin"})

        for field, value in update_data.items():
            if hasattr(user, field):
                setattr(user, field, value)

        if body.is_admin is not None:
            if actor.id == user.id:
                raise BadRequestError("You cannot change your own admin access.")
            AdminUserService._set_admin_access(user, body.is_admin)

        await db.commit()
        await db.refresh(user)
        logger.info("Admin id=%s updated user id=%s", actor.id, user.id)
        return user

    @staticmethod
    async def toggle_admin_access(
        db: AsyncSession,
        *,
        actor: User,
        user_id: int,
    ) -> User:
        user = await AdminUserService.get_user(db, user_id)

        if actor.id == user.id:
            raise BadRequestError("You cannot change your own admin access.")

        AdminUserService._set_admin_access(user, not user_is_admin(user))
        await db.commit()
        await db.refresh(user)
        logger.info("Admin id=%s toggled admin access for user id=%s", actor.id, user.id)
        return user

    @staticmethod
    async def update_subscription(
        db: AsyncSession,
        *,
        user_id: int,
        body: AdminUserSubscriptionUpdateRequest,
    ) -> User:
        user = await AdminUserService.get_user(db, user_id)
        tier = body.tier.upper()

        if tier not in PLAN_FEATURES:
            raise BadRequestError(f"Unsupported subscription tier: {tier}")

        subscription = user.subscription
        if subscription is None:
            subscription = Subscription(user_id=user.id)
            db.add(subscription)

        subscription.tier = tier
        subscription.status = "active"
        subscription.features = PLAN_FEATURES[tier]

        now = datetime.now(timezone.utc)
        if tier == "FREE":
            subscription.expires_at = None
        elif tier == "PRO":
            current_expiry = (
                subscription.expires_at
                if subscription.expires_at and subscription.expires_at > now
                else now
            )
            subscription.expires_at = current_expiry + timedelta(days=30)
        else:
            subscription.expires_at = None

        await db.commit()
        await db.refresh(user)
        logger.info("Admin updated subscription tier=%s for user id=%s", tier, user.id)
        return user

    @staticmethod
    async def deactivate_user(
        db: AsyncSession,
        *,
        actor: User,
        user_id: int,
    ) -> User:
        user = await AdminUserService.get_user(db, user_id)

        if actor.id == user.id:
            raise BadRequestError("You cannot deactivate your own account.")

        if user.deleted_at is None:
            user.deleted_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(user)
        logger.info("Admin id=%s deactivated user id=%s", actor.id, user.id)
        return user

    @staticmethod
    async def restore_user(
        db: AsyncSession,
        *,
        user_id: int,
    ) -> User:
        user = await AdminUserService.get_user(db, user_id)
        user.deleted_at = None
        await db.commit()
        await db.refresh(user)
        logger.info("Restored user id=%s", user.id)
        return user

    @staticmethod
    def _apply_role_filter(users: list[User], role: str | None) -> list[User]:
        normalized_role = (role or "").strip().lower()
        if normalized_role == "admin":
            return [user for user in users if user_is_admin(user)]
        if normalized_role in {"learner", "member", "user"}:
            return [user for user in users if not user_is_admin(user)]
        return users

    @staticmethod
    def _set_admin_access(user: User, is_admin: bool) -> None:
        preferences = dict(user.preferences or {})
        preferences["is_admin"] = is_admin
        if is_admin:
            preferences["role"] = "admin"
        elif preferences.get("role") == "admin":
            preferences.pop("role", None)
        user.preferences = preferences

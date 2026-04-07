from __future__ import annotations

from app.modules.users.models.user import User
from app.modules.users.schemas.admin_user import AdminUserRead
from app.modules.users.schemas.user import UserRead


def user_is_admin(user: User) -> bool:
    preferences = user.preferences or {}
    return bool(preferences.get("is_admin") or preferences.get("role") == "admin")


def _build_user_payload(user: User) -> dict[str, object]:
    return {
        "id": user.id,
        "email": user.email,
        "auth_provider": user.auth_provider,
        "has_password": bool(user.password_hash),
        "is_admin": user_is_admin(user),
        "display_name": user.display_name,
        "avatar": user.avatar,
        "age": user.age,
        "native_language": user.native_language,
        "target_language": user.target_language,
        "level": user.level,
        "favorite_topics": user.favorite_topics,
        "learning_purpose": user.learning_purpose,
        "main_challenge": user.main_challenge,
        "daily_goal": user.daily_goal,
        "is_onboarding_completed": user.is_onboarding_completed,
        "preferences": user.preferences or {},
        "subscription": user.subscription,
        "created_at": user.created_at,
        "updated_at": user.updated_at,
    }


def serialize_user(user: User) -> UserRead:
    return UserRead.model_validate(_build_user_payload(user))


def serialize_admin_user(user: User) -> AdminUserRead:
    return AdminUserRead.model_validate(
        {
            **_build_user_payload(user),
            "deleted_at": user.deleted_at,
        }
    )

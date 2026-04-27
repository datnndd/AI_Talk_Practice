from __future__ import annotations

from datetime import datetime, timezone

from app.modules.gamification.settings import GamificationRules, default_rules, level_progress_from_total_xp
from app.modules.users.models.user import User
from app.modules.users.schemas.admin_user import AdminUserRead
from app.modules.users.schemas.user import UserRead


def user_is_admin(user: User) -> bool:
    preferences = user.preferences or {}
    return bool(preferences.get("is_admin") or preferences.get("role") == "admin")


def _admin_gamification_payload(user: User, rules: GamificationRules) -> dict[str, object]:
    today = datetime.now(timezone.utc).date()
    today_stat = next((item for item in getattr(user, "daily_stats", []) if item.date == today), None)
    total_xp = user.total_xp or 0
    progress = level_progress_from_total_xp(total_xp)
    today_checkin = next((item for item in getattr(user, "daily_checkins", []) if item.date == today), None)
    return {
        "xp": {
            "total": total_xp,
            "today": today_stat.xp_earned if today_stat else 0,
            "level": progress.level,
            "level_progress": progress.level_progress,
            "level_size": progress.level_size,
            "xp_to_next_level": progress.xp_to_next_level,
        },
        "coin": {"balance": user.coin_balance or 0},
        "check_in": {
            "checked_in_today": today_checkin is not None,
            "current_streak": today_checkin.streak_day if today_checkin else 0,
            "today_coin_reward": today_checkin.coin_earned if today_checkin else 0,
        },
    }


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


def serialize_admin_user(user: User, rules: GamificationRules | None = None) -> AdminUserRead:
    return AdminUserRead.model_validate(
        {
            **_build_user_payload(user),
            "deleted_at": user.deleted_at,
            "gamification": _admin_gamification_payload(user, rules or default_rules()),
        }
    )

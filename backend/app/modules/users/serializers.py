from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.modules.gamification.settings import GamificationRules, XP_PER_LEVEL, default_rules
from app.modules.users.models.user import User
from app.modules.users.schemas.admin_user import AdminUserRead
from app.modules.users.schemas.user import UserRead


def user_is_admin(user: User) -> bool:
    preferences = user.preferences or {}
    return bool(preferences.get("is_admin") or preferences.get("role") == "admin")


def user_has_unlimited_hearts(user: User) -> bool:
    subscription = getattr(user, "subscription", None)
    return bool(subscription and subscription.tier in {"PRO", "ENTERPRISE"} and subscription.status == "active")


def _admin_gamification_payload(user: User, rules: GamificationRules) -> dict[str, object]:
    today = datetime.now(timezone.utc).date()
    today_stat = next((item for item in getattr(user, "daily_stats", []) if item.date == today), None)
    is_unlimited = user_has_unlimited_hearts(user)
    next_refill_at = None
    if not is_unlimited and (user.heart_balance or 0) < (user.heart_max or 5):
        last_refill = user.last_heart_refill_at or datetime.now(timezone.utc)
        if last_refill.tzinfo is None:
            last_refill = last_refill.replace(tzinfo=timezone.utc)
        next_refill_at = last_refill + timedelta(minutes=rules.heart_refill_minutes)

    unlocked = []
    for user_achievement in getattr(user, "achievements", []):
        achievement = user_achievement.achievement
        unlocked.append(
            {
                "code": achievement.code,
                "name": achievement.name,
                "description": achievement.description,
                "gem_reward": achievement.gem_reward,
                "icon": achievement.icon_url,
                "unlocked_at": user_achievement.unlocked_at,
            }
        )

    total_xp = user.total_xp or 0
    return {
        "streak": {
            "current": user.current_streak or 0,
            "longest": user.longest_streak or 0,
            "last_completed_lesson_date": user.last_completed_lesson_date,
        },
        "xp": {
            "total": total_xp,
            "today": today_stat.xp_earned if today_stat else 0,
            "level": (total_xp // XP_PER_LEVEL) + 1,
            "level_progress": total_xp % XP_PER_LEVEL,
        },
        "gem": {"balance": user.gem_balance or 0},
        "heart": {
            "current": None if is_unlimited else user.heart_balance,
            "max": user.heart_max or 5,
            "is_unlimited": is_unlimited,
            "next_refill_at": next_refill_at,
        },
        "achievements": {"unlocked": unlocked},
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

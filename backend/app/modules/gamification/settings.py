from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification.models.gamification_setting import GamificationSetting

XP_PER_LEVEL = 1000
DEFAULT_XP_PER_GEM = 10
DEFAULT_HEART_REFILL_MINUTES = 60
LESSON_TYPES = {"basic", "vocabulary", "listening", "reading", "writing", "speaking", "speaking_short"}
SPEAKING_LESSON_TYPES = {"speaking", "speaking_short"}
ALLOWED_ACHIEVEMENT_CONDITION_FIELDS = {
    "current_streak",
    "total_xp",
    "total_lessons_completed",
    "total_speaking_lessons_completed",
    "total_vocabulary_lessons_completed",
    "daily_goal_streak",
    "perfect_score_count",
}

DEFAULT_XP_BY_LESSON_TYPE = {
    "vocabulary": 10,
    "listening": 15,
    "reading": 15,
    "writing": 15,
    "basic": 20,
    "speaking_short": 20,
    "speaking": 30,
}
DEFAULT_HEART_PURCHASE_PRICES = {"1": 10, "5": 40}


@dataclass(frozen=True)
class GamificationRules:
    xp_by_lesson_type: dict[str, int]
    xp_per_gem: int
    heart_purchase_prices: dict[str, int]
    heart_refill_minutes: int


def default_rules() -> GamificationRules:
    return GamificationRules(
        xp_by_lesson_type=dict(DEFAULT_XP_BY_LESSON_TYPE),
        xp_per_gem=DEFAULT_XP_PER_GEM,
        heart_purchase_prices=dict(DEFAULT_HEART_PURCHASE_PRICES),
        heart_refill_minutes=DEFAULT_HEART_REFILL_MINUTES,
    )


async def get_effective_rules(db: AsyncSession) -> GamificationRules:
    rules = default_rules()
    result = await db.execute(select(GamificationSetting))
    rows = {item.key: item.value for item in result.scalars().all()}

    xp_by_lesson_type = dict(rules.xp_by_lesson_type)
    xp_by_lesson_type.update({str(key): int(value) for key, value in (rows.get("xp_by_lesson_type") or {}).items()})

    heart_purchase_prices = dict(rules.heart_purchase_prices)
    heart_purchase_prices.update(
        {str(key): int(value) for key, value in (rows.get("heart_purchase_prices") or {}).items()}
    )

    return GamificationRules(
        xp_by_lesson_type=xp_by_lesson_type,
        xp_per_gem=int(rows.get("xp_per_gem") or rules.xp_per_gem),
        heart_purchase_prices=heart_purchase_prices,
        heart_refill_minutes=int(rows.get("heart_refill_minutes") or rules.heart_refill_minutes),
    )

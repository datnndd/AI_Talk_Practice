from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.gamification.models.gamification_setting import GamificationSetting

DEFAULT_DAILY_CHECKIN_COIN_REWARDS = {"1": 1}
DEFAULT_LEVEL_COIN_REWARDS: dict[str, int] = {}
SHOP_ITEMS = {
    "pro_1_day_ticket": {
        "code": "pro_1_day_ticket",
        "name": "Pro 1 day ticket",
        "description": "Unlocks Pro access for 1 day.",
        "price_coin": 500,
        "type": "subscription_ticket",
        "duration_days": 1,
    }
}


@dataclass(frozen=True)
class LevelProgress:
    level: int
    level_progress: int
    level_size: int
    xp_to_next_level: int


@dataclass(frozen=True)
class GamificationRules:
    level_coin_rewards: dict[str, int]
    daily_checkin_coin_rewards: dict[str, int]


def xp_required_for_level(level: int) -> int:
    """XP needed to move from level N to N+1."""
    normalized = max(1, int(level))
    return 100 * (((normalized - 1) // 10) + 1)


def level_progress_from_total_xp(total_xp: int) -> LevelProgress:
    remaining = max(0, int(total_xp or 0))
    level = 1
    while True:
        level_size = xp_required_for_level(level)
        if remaining < level_size:
            return LevelProgress(
                level=level,
                level_progress=remaining,
                level_size=level_size,
                xp_to_next_level=level_size - remaining,
            )
        remaining -= level_size
        level += 1


def level_from_total_xp(total_xp: int) -> int:
    return level_progress_from_total_xp(total_xp).level


def tiered_coin_reward(rewards: dict[str, int], streak_day: int) -> int:
    eligible = [int(key) for key in rewards if str(key).isdigit() and int(key) <= streak_day]
    if not eligible:
        return 0
    return int(rewards[str(max(eligible))])


def default_rules() -> GamificationRules:
    return GamificationRules(
        level_coin_rewards=dict(DEFAULT_LEVEL_COIN_REWARDS),
        daily_checkin_coin_rewards=dict(DEFAULT_DAILY_CHECKIN_COIN_REWARDS),
    )


async def get_effective_rules(db: AsyncSession) -> GamificationRules:
    rules = default_rules()
    result = await db.execute(select(GamificationSetting))
    rows = {item.key: item.value for item in result.scalars().all()}

    level_coin_rewards = dict(rules.level_coin_rewards)
    level_coin_rewards.update(
        {str(key): int(value) for key, value in (rows.get("level_coin_rewards") or {}).items()}
    )

    daily_checkin_coin_rewards = dict(rules.daily_checkin_coin_rewards)
    daily_checkin_coin_rewards.update(
        {str(key): int(value) for key, value in (rows.get("daily_checkin_coin_rewards") or {}).items()}
    )

    return GamificationRules(
        level_coin_rewards=level_coin_rewards,
        daily_checkin_coin_rewards=daily_checkin_coin_rewards,
    )

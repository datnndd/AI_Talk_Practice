from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


LeaderboardPeriod = Literal["weekly", "all_time"]


class XPRead(BaseModel):
    total: int
    today: int
    level: int
    level_progress: int
    level_size: int
    xp_to_next_level: int


class CoinRead(BaseModel):
    balance: int


class CheckInRead(BaseModel):
    checked_in_today: bool
    current_streak: int
    today_coin_reward: int


class GamificationDashboard(BaseModel):
    xp: XPRead
    coin: CoinRead
    check_in: CheckInRead


class RewardRead(BaseModel):
    xp_earned: int
    coin_earned: int
    levels_gained: int = 0
    level_coin_reward: int = 0


class LessonCompleteResponse(BaseModel):
    reward: RewardRead
    dashboard: GamificationDashboard


class CheckInResponse(BaseModel):
    date: date
    streak_day: int
    coin_earned: int
    dashboard: GamificationDashboard


class ShopItemRead(BaseModel):
    code: str
    name: str
    description: str
    price_coin: int
    type: str
    duration_days: int | None = None


class ShopRead(BaseModel):
    items: list[ShopItemRead]


class ShopPurchaseRequest(BaseModel):
    item_code: str = Field(min_length=1, max_length=80)


class ShopPurchaseResponse(BaseModel):
    item: ShopItemRead
    coin_spent: int
    subscription_expires_at: datetime | None = None
    dashboard: GamificationDashboard


class LeaderboardEntryRead(BaseModel):
    user_id: int
    rank: int
    score: int
    display_name: str | None = None
    email: str
    avatar: str | None = None


class LeaderboardRead(BaseModel):
    period: LeaderboardPeriod
    entries: list[LeaderboardEntryRead]
    current_user: LeaderboardEntryRead
    available_periods: list[LeaderboardPeriod] = Field(default_factory=lambda: ["weekly", "all_time"])

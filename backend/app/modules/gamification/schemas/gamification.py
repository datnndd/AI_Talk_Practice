from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


LeaderboardPeriod = Literal["weekly"]


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
    already_checked_in: bool = False


class ShopItemRead(BaseModel):
    id: int
    code: str
    name: str
    description: str
    price_coin: int
    image_url: str | None = None
    stock_quantity: int
    is_active: bool = True
    sort_order: int = 0


class ShopRead(BaseModel):
    items: list[ShopItemRead]


class ShopRedeemRequest(BaseModel):
    product_code: str = Field(min_length=1, max_length=80)
    recipient_name: str = Field(min_length=1, max_length=160)
    phone: str = Field(min_length=1, max_length=40)
    address: str = Field(min_length=1, max_length=1000)
    note: str | None = Field(default=None, max_length=1000)


class ShopRedemptionRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    price_coin: int
    recipient_name: str
    phone: str
    address: str
    note: str | None = None
    status: str
    refunded: bool = False
    created_at: datetime


class ShopRedeemResponse(BaseModel):
    item: ShopItemRead
    redemption: ShopRedemptionRead
    coin_spent: int
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
    available_periods: list[LeaderboardPeriod] = Field(default_factory=lambda: ["weekly"])

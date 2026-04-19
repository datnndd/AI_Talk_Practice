from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


LessonType = Literal["basic", "vocabulary", "listening", "reading", "writing", "speaking", "speaking_short"]


class AchievementRead(BaseModel):
    code: str
    name: str
    description: str
    gem_reward: int
    icon: str | None = None


class UnlockedAchievementRead(AchievementRead):
    unlocked_at: datetime


class StreakRead(BaseModel):
    current: int
    longest: int
    last_completed_lesson_date: date | None = None


class XPRead(BaseModel):
    total: int
    today: int
    daily_goal: int
    level: int
    level_progress: int
    level_size: int = 1000
    daily_goal_met: bool


class GemRead(BaseModel):
    balance: int


class HeartRead(BaseModel):
    current: int | None
    max: int
    is_unlimited: bool
    next_refill_at: datetime | None = None


class AchievementSummaryRead(BaseModel):
    available: list[AchievementRead]
    unlocked: list[UnlockedAchievementRead]


class GamificationDashboard(BaseModel):
    streak: StreakRead
    xp: XPRead
    gem: GemRead
    heart: HeartRead
    achievements: AchievementSummaryRead


class RewardRead(BaseModel):
    xp_earned: int
    gem_earned: int


class LessonCompleteRequest(BaseModel):
    lesson_type: LessonType
    score: float | None = Field(default=None, ge=0, le=100)


class LessonCompleteResponse(BaseModel):
    reward: RewardRead
    unlocked_achievements: list[UnlockedAchievementRead]
    dashboard: GamificationDashboard


class HeartPurchaseRequest(BaseModel):
    hearts: Literal[1, 5]


class HeartPurchaseResponse(BaseModel):
    hearts_added: int
    gem_spent: int
    dashboard: GamificationDashboard


class DailyGoalUpdateRequest(BaseModel):
    daily_xp_goal: Literal[30, 50, 100, 150]

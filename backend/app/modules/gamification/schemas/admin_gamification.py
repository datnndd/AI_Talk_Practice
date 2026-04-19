from __future__ import annotations

from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.gamification.settings import ALLOWED_ACHIEVEMENT_CONDITION_FIELDS, LESSON_TYPES


def _validate_positive_int_map(value: dict[str, int] | None, *, allowed_keys: set[str] | None = None) -> dict[str, int] | None:
    if value is None:
        return None
    normalized: dict[str, int] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key)
        if allowed_keys is not None and key not in allowed_keys:
            raise ValueError(f"Unsupported key: {key}")
        amount = int(raw_value)
        if amount <= 0:
            raise ValueError(f"{key} must be a positive integer")
        normalized[key] = amount
    return normalized


def _validate_condition(value: dict[str, Any]) -> dict[str, int]:
    normalized: dict[str, int] = {}
    for raw_field, raw_expected in value.items():
        field = str(raw_field)
        if field not in ALLOWED_ACHIEVEMENT_CONDITION_FIELDS:
            raise ValueError(f"Unsupported achievement condition field: {field}")
        expected = int(raw_expected)
        if expected <= 0:
            raise ValueError(f"{field} must be a positive integer")
        normalized[field] = expected
    return normalized


class GamificationSettingsRead(BaseModel):
    xp_by_lesson_type: dict[str, int]
    xp_per_gem: int
    heart_purchase_prices: dict[str, int]
    heart_refill_minutes: int


class GamificationSettingsUpdateRequest(BaseModel):
    xp_by_lesson_type: dict[str, int] | None = None
    xp_per_gem: int | None = Field(default=None, gt=0)
    heart_purchase_prices: dict[str, int] | None = None
    heart_refill_minutes: int | None = Field(default=None, gt=0)
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("xp_by_lesson_type")
    @classmethod
    def validate_xp_by_lesson_type(cls, value: dict[str, int] | None) -> dict[str, int] | None:
        return _validate_positive_int_map(value, allowed_keys=LESSON_TYPES)

    @field_validator("heart_purchase_prices")
    @classmethod
    def validate_heart_purchase_prices(cls, value: dict[str, int] | None) -> dict[str, int] | None:
        return _validate_positive_int_map(value, allowed_keys={"1", "5"})

    @model_validator(mode="after")
    def validate_non_empty_payload(self) -> "GamificationSettingsUpdateRequest":
        if not (self.xp_by_lesson_type or self.xp_per_gem or self.heart_purchase_prices or self.heart_refill_minutes):
            raise ValueError("At least one gamification setting must be provided")
        return self


class AchievementAdminRead(BaseModel):
    id: int
    code: str
    name: str
    description: str
    icon: str | None = None
    gem_reward: int
    condition: dict[str, int]
    is_active: bool
    deleted_at: datetime | None = None


class AchievementCreateRequest(BaseModel):
    code: str = Field(min_length=1, max_length=50, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=255)
    icon: str | None = Field(default=None, max_length=500)
    gem_reward: int = Field(ge=0)
    condition: dict[str, Any]
    is_active: bool = True

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: dict[str, Any]) -> dict[str, int]:
        return _validate_condition(value)


class AchievementUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=255)
    icon: str | None = Field(default=None, max_length=500)
    gem_reward: int | None = Field(default=None, ge=0)
    condition: dict[str, Any] | None = None
    is_active: bool | None = None

    @field_validator("condition")
    @classmethod
    def validate_condition(cls, value: dict[str, Any] | None) -> dict[str, int] | None:
        if value is None:
            return None
        return _validate_condition(value)

    @model_validator(mode="after")
    def validate_non_empty_payload(self) -> "AchievementUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one achievement field must be provided")
        return self


class AchievementListResponse(BaseModel):
    items: list[AchievementAdminRead]
    total: int


class AdminGamificationOverviewRead(BaseModel):
    date: date
    active_users_today: int
    streak_retention_rate: float
    speaking_sessions_started: int
    gems_in_circulation: int
    pro_upgrade_rate: float

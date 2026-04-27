from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field, field_validator, model_validator


def _validate_non_negative_int_map(value: dict[str, int] | None) -> dict[str, int] | None:
    if value is None:
        return None
    normalized: dict[str, int] = {}
    for raw_key, raw_value in value.items():
        key = str(raw_key)
        if not key.isdigit() or int(key) <= 0:
            raise ValueError(f"Unsupported key: {key}")
        amount = int(raw_value)
        if amount < 0:
            raise ValueError(f"{key} must be a non-negative integer")
        normalized[key] = amount
    return normalized


class GamificationSettingsRead(BaseModel):
    level_coin_rewards: dict[str, int]
    daily_checkin_coin_rewards: dict[str, int]


class GamificationSettingsUpdateRequest(BaseModel):
    level_coin_rewards: dict[str, int] | None = None
    daily_checkin_coin_rewards: dict[str, int] | None = None
    reason: str | None = Field(default=None, max_length=500)

    @field_validator("level_coin_rewards", "daily_checkin_coin_rewards")
    @classmethod
    def validate_rewards(cls, value: dict[str, int] | None) -> dict[str, int] | None:
        return _validate_non_negative_int_map(value)

    @model_validator(mode="after")
    def validate_non_empty_payload(self) -> "GamificationSettingsUpdateRequest":
        if self.level_coin_rewards is None and self.daily_checkin_coin_rewards is None:
            raise ValueError("At least one gamification setting must be provided")
        return self


class AdminGamificationOverviewRead(BaseModel):
    date: date
    active_users_today: int
    checkins_today: int
    coins_in_circulation: int
    pro_upgrade_rate: float

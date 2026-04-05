from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SubscriptionRead(BaseModel):
    tier: str
    status: str
    expires_at: datetime | None = None
    features: dict[str, Any] | None = None

    model_config = ConfigDict(from_attributes=True)


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _normalize_string_list(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",") if item.strip()]
        return values if len(values) > 1 else (values[0] if values else None)
    return value


class OnboardingRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    native_language: str = Field(default="vi", max_length=10)
    target_language: str | None = Field(default=None, max_length=10)
    avatar: str | None = Field(default=None, max_length=500)
    age: int | None = Field(default=None, ge=1, le=120)
    level: str = Field(
        default="beginner",
        pattern=r"^(A1|A2|B1|B2|C1|C2|beginner|intermediate|advanced)$",
    )
    learning_purpose: Any | None = None
    main_challenge: str | None = Field(default=None, max_length=500)
    favorite_topics: list[str] | str | None = None
    daily_goal: int | None = Field(default=None, ge=1, le=1440)
    preferences: dict[str, Any] | None = None

    @field_validator("favorite_topics", "learning_purpose", mode="before")
    @classmethod
    def normalize_list_like_fields(cls, value: Any) -> Any:
        return _normalize_string_list(value)


class UserRead(ORMModel):
    id: int
    email: str
    is_admin: bool = False
    display_name: str | None = None
    avatar: str | None = None
    age: int | None = None
    native_language: str | None = None
    target_language: str | None = None
    level: str | None = None
    favorite_topics: Any | None = None
    learning_purpose: Any | None = None
    main_challenge: str | None = None
    daily_goal: int | None = None
    is_onboarding_completed: bool
    preferences: dict[str, Any] | None = None
    subscription: SubscriptionRead | None = None
    created_at: datetime
    updated_at: datetime

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.modules.users.schemas.user import UserRead


def _normalize_string_list(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        values = [item.strip() for item in value.split(",") if item.strip()]
        return values if len(values) > 1 else (values[0] if values else None)
    return value


def _normalize_optional_string(value: Any) -> Any:
    if isinstance(value, str):
        stripped = value.strip()
        return stripped or None
    return value


class AdminUserRead(UserRead):
    deleted_at: datetime | None = None
    gamification: dict[str, Any] | None = None


class AdminUserListResponse(BaseModel):
    items: list[AdminUserRead]
    total: int
    page: int
    page_size: int


class AdminUserUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, min_length=1, max_length=100)
    native_language: str | None = Field(default=None, max_length=10)
    target_language: str | None = Field(default=None, max_length=10)
    avatar: str | None = Field(default=None, max_length=500)
    age: int | None = Field(default=None, ge=1, le=120)
    level: str | None = Field(
        default=None,
        pattern=r"^(A1|A2|B1|B2|C1|C2|beginner|intermediate|advanced)$",
    )
    learning_purpose: Any | None = None
    main_challenge: str | None = Field(default=None, max_length=500)
    favorite_topics: list[str] | str | None = None
    daily_goal: int | None = Field(default=None, ge=1, le=1440)
    is_admin: bool | None = None

    @field_validator("favorite_topics", "learning_purpose", mode="before")
    @classmethod
    def normalize_list_like_fields(cls, value: Any) -> Any:
        return _normalize_string_list(value)

    @field_validator(
        "display_name",
        "native_language",
        "target_language",
        "avatar",
        "main_challenge",
        mode="before",
    )
    @classmethod
    def normalize_optional_strings(cls, value: Any) -> Any:
        return _normalize_optional_string(value)

    @model_validator(mode="after")
    def validate_non_empty_payload(self) -> "AdminUserUpdateRequest":
        if not self.model_fields_set:
            raise ValueError("At least one user field must be provided")
        return self


class AdminUserSubscriptionUpdateRequest(BaseModel):
    tier: Literal["FREE", "PRO", "ENTERPRISE"]


class AdminUserResetStreakRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=500)


class AdminUserBalanceAdjustmentRequest(BaseModel):
    gem_delta: int | None = None
    heart_delta: int | None = None
    reason: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def validate_non_empty_payload(self) -> "AdminUserBalanceAdjustmentRequest":
        if self.gem_delta is None and self.heart_delta is None:
            raise ValueError("gem_delta or heart_delta must be provided")
        return self

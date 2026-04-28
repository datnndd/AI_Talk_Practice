from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


def _parse_jsonish(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        return json.loads(stripped)
    return value


def _normalize_string_list(value: Any) -> list[str]:
    parsed = _parse_jsonish(value) if isinstance(value, str) else value
    if parsed is None:
        return []
    if isinstance(parsed, str):
        return [item.strip() for item in parsed.split(",") if item.strip()]
    if isinstance(parsed, list):
        return [str(item).strip() for item in parsed if str(item).strip()]
    raise ValueError("Expected a list of strings")


class PromptQualityAssessment(BaseModel):
    score: int = Field(ge=0, le=100)
    is_acceptable: bool
    warnings: list[str] = Field(default_factory=list)
    suggestions: list[str] = Field(default_factory=list)


class ScenarioAdminBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20)
    category: str = Field(min_length=2, max_length=50)
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard)$")
    ai_system_prompt: str = ""
    ai_role: str = Field(default="", max_length=500)
    user_role: str = Field(default="", max_length=500)
    tasks: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = Field(default=10, ge=1, le=180)
    is_active: bool = True
    is_pro: bool = False
    image_url: str | None = None

    @field_validator("tasks", "tags", mode="before")
    @classmethod
    def parse_list_fields(cls, value: Any) -> list[str]:
        return _normalize_string_list(value)


class ScenarioAdminCreate(ScenarioAdminBase):
    pass


class ScenarioAdminUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, min_length=20)
    category: str | None = Field(default=None, min_length=2, max_length=50)
    difficulty: str | None = Field(default=None, pattern=r"^(easy|medium|hard)$")
    ai_system_prompt: str | None = None
    ai_role: str | None = Field(default=None, max_length=500)
    user_role: str | None = Field(default=None, max_length=500)
    tasks: list[str] | None = None
    tags: list[str] | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=180)
    is_active: bool | None = None
    is_pro: bool | None = None
    image_url: str | None = None

    @field_validator("tasks", "tags", mode="before")
    @classmethod
    def parse_optional_list_fields(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return _normalize_string_list(value)


class ScenarioAdminRead(ORMModel):
    id: int
    title: str
    description: str
    category: str
    difficulty: str
    ai_system_prompt: str
    ai_role: str = ""
    user_role: str = ""
    tasks: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = None
    is_active: bool
    is_pro: bool
    image_url: str | None = None
    deleted_at: datetime | None = None
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime


class ScenarioListResponse(BaseModel):
    items: list[ScenarioAdminRead]
    total: int
    page: int
    page_size: int


class GenerateDefaultPromptRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20)
    ai_role: str = Field(default="", max_length=500)
    user_role: str = Field(default="", max_length=500)
    tasks: list[str] = Field(default_factory=list)

    @field_validator("tasks", mode="before")
    @classmethod
    def parse_prompt_list_fields(cls, value: Any) -> list[str]:
        return _normalize_string_list(value)


class GenerateDefaultPromptResponse(BaseModel):
    prompt: str
    quality: PromptQualityAssessment


class BulkScenarioActionRequest(BaseModel):
    scenario_ids: list[int] = Field(min_length=1)
    action: str = Field(pattern=r"^(activate|deactivate|soft_delete)$")


class BulkScenarioActionResponse(BaseModel):
    success: bool
    message: str

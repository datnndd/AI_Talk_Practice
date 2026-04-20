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
    recommended_target_skills: list[str] = Field(default_factory=list)


class PromptHistoryRead(ORMModel):
    id: int
    scenario_id: int
    previous_prompt: str
    new_prompt: str
    change_note: str | None = None
    quality_score: int | None = None
    changed_by: int | None = None
    created_at: datetime
    updated_at: datetime


class ScenarioAdminBase(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20)
    category: str = Field(min_length=2, max_length=50)
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard)$")
    ai_system_prompt: str = ""
    ai_role: str = Field(default="", max_length=500)
    user_role: str = Field(default="", max_length=500)
    learning_objectives: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = Field(default=10, ge=1, le=180)
    mode: str = Field(
        default="conversation",
        pattern=r"^(conversation|roleplay|debate|interview|presentation)$",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    change_note: str | None = Field(default=None, max_length=255)

    @field_validator("learning_objectives", "target_skills", "tags", mode="before")
    @classmethod
    def parse_list_fields(cls, value: Any) -> list[str]:
        return _normalize_string_list(value)

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_metadata(cls, value: Any) -> dict[str, Any]:
        parsed = _parse_jsonish(value)
        return parsed or {}


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
    learning_objectives: list[str] | None = None
    target_skills: list[str] | None = None
    tags: list[str] | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=180)
    mode: str | None = Field(
        default=None,
        pattern=r"^(conversation|roleplay|debate|interview|presentation)$",
    )
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None
    change_note: str | None = Field(default=None, max_length=255)

    @field_validator("learning_objectives", "target_skills", "tags", mode="before")
    @classmethod
    def parse_optional_list_fields(cls, value: Any) -> list[str] | None:
        if value is None:
            return None
        return _normalize_string_list(value)

    @field_validator("metadata", mode="before")
    @classmethod
    def parse_optional_metadata(cls, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        parsed = _parse_jsonish(value)
        return parsed or {}


class ScenarioAdminRead(ORMModel):
    id: int
    title: str
    description: str
    category: str
    difficulty: str
    ai_system_prompt: str
    ai_role: str = ""
    user_role: str = ""
    learning_objectives: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = None
    mode: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    deleted_at: datetime | None = None
    created_by: int | None = None
    usage_count: int = 0
    latest_prompt_quality: PromptQualityAssessment | None = None
    prompt_history: list[PromptHistoryRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ScenarioListResponse(BaseModel):
    items: list[ScenarioAdminRead]
    total: int
    page: int
    page_size: int


class SuggestSkillsRequest(BaseModel):
    description: str = Field(min_length=10)
    category: str | None = Field(default=None, max_length=50)


class SuggestSkillsResponse(BaseModel):
    suggested_skills: list[str]


class GenerateDefaultPromptRequest(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=20)
    ai_role: str = Field(default="", max_length=500)
    user_role: str = Field(default="", max_length=500)
    mode: str = Field(
        default="conversation",
        pattern=r"^(conversation|roleplay|debate|interview|presentation)$",
    )
    learning_objectives: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)

    @field_validator("learning_objectives", "target_skills", mode="before")
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

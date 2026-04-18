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
    ai_system_prompt: str = Field(min_length=40)
    opening_message: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = Field(default=10, ge=1, le=180)
    is_pre_generated: bool = False
    pre_gen_count: int = Field(default=8, ge=0, le=30)
    mode: str = Field(
        default="conversation",
        pattern=r"^(conversation|roleplay|debate|interview|presentation)$",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True
    is_ai_start_first: bool = True
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
    ai_system_prompt: str | None = Field(default=None, min_length=40)
    opening_message: str | None = None
    learning_objectives: list[str] | None = None
    target_skills: list[str] | None = None
    tags: list[str] | None = None
    estimated_duration_minutes: int | None = Field(default=None, ge=1, le=180)
    is_pre_generated: bool | None = None
    pre_gen_count: int | None = Field(default=None, ge=0, le=30)
    mode: str | None = Field(
        default=None,
        pattern=r"^(conversation|roleplay|debate|interview|presentation)$",
    )
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None
    is_ai_start_first: bool | None = None
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


class ScenarioVariationAdminBase(BaseModel):
    scenario_id: int
    variation_name: str = Field(min_length=2, max_length=160)
    parameters: dict[str, Any] = Field(default_factory=dict)
    sample_prompt: str | None = Field(default=None, max_length=500)
    sample_conversation: list[dict[str, Any]] = Field(default_factory=list)
    system_prompt_override: str | None = None
    is_active: bool = True
    is_pregenerated: bool = False
    is_approved: bool = False

    @field_validator("parameters", mode="before")
    @classmethod
    def parse_parameters(cls, value: Any) -> dict[str, Any]:
        parsed = _parse_jsonish(value)
        return parsed or {}

    @field_validator("sample_conversation", mode="before")
    @classmethod
    def parse_sample_conversation(cls, value: Any) -> list[dict[str, Any]]:
        parsed = _parse_jsonish(value)
        return parsed or []


class ScenarioVariationAdminCreate(ScenarioVariationAdminBase):
    variation_seed: str | None = Field(default=None, min_length=8, max_length=64)


class ScenarioVariationAdminUpdate(BaseModel):
    variation_name: str | None = Field(default=None, min_length=2, max_length=160)
    parameters: dict[str, Any] | None = None
    sample_prompt: str | None = Field(default=None, max_length=500)
    sample_conversation: list[dict[str, Any]] | None = None
    system_prompt_override: str | None = None
    is_active: bool | None = None
    is_pregenerated: bool | None = None
    is_approved: bool | None = None

    @field_validator("parameters", mode="before")
    @classmethod
    def parse_optional_parameters(cls, value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        parsed = _parse_jsonish(value)
        return parsed or {}

    @field_validator("sample_conversation", mode="before")
    @classmethod
    def parse_optional_sample_conversation(cls, value: Any) -> list[dict[str, Any]] | None:
        if value is None:
            return None
        parsed = _parse_jsonish(value)
        return parsed or []


class ScenarioVariationAdminRead(ORMModel):
    id: int
    scenario_id: int
    variation_seed: str
    variation_name: str
    parameters: dict[str, Any]
    sample_prompt: str | None = None
    sample_conversation: list[dict[str, Any]] = Field(default_factory=list)
    system_prompt_override: str | None = None
    is_active: bool
    is_pregenerated: bool
    is_approved: bool
    generated_by_model: str | None = None
    generation_latency_ms: int | None = None
    usage_count: int
    last_used_at: datetime | None = None
    created_at: datetime
    updated_at: datetime


class ScenarioAdminRead(ORMModel):
    id: int
    title: str
    description: str
    category: str
    difficulty: str
    ai_system_prompt: str
    opening_message: str | None = None
    learning_objectives: list[str] = Field(default_factory=list)
    target_skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    estimated_duration_minutes: int | None = None
    is_pre_generated: bool
    pre_gen_count: int
    mode: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool
    is_ai_start_first: bool
    deleted_at: datetime | None = None
    created_by: int | None = None
    usage_count: int = 0
    variation_count: int = 0
    active_variation_count: int = 0
    latest_prompt_quality: PromptQualityAssessment | None = None
    variations: list[ScenarioVariationAdminRead] = Field(default_factory=list)
    prompt_history: list[PromptHistoryRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class ScenarioListResponse(BaseModel):
    items: list[ScenarioAdminRead]
    total: int
    page: int
    page_size: int


class VariationListResponse(BaseModel):
    items: list[ScenarioVariationAdminRead]
    total: int


class SuggestSkillsRequest(BaseModel):
    description: str = Field(min_length=10)
    category: str | None = Field(default=None, max_length=50)


class SuggestSkillsResponse(BaseModel):
    suggested_skills: list[str]


class BulkScenarioActionRequest(BaseModel):
    scenario_ids: list[int] = Field(min_length=1)
    action: str = Field(pattern=r"^(activate|deactivate|soft_delete|generate_variations)$")
    generation_count: int | None = Field(default=None, ge=1, le=20)


class BulkScenarioActionResponse(BaseModel):
    success: bool
    message: str
    task: "GenerationTaskRead | None" = None


class GenerateVariationsRequest(BaseModel):
    count: int = Field(default=8, ge=1, le=20)
    overwrite_existing: bool = False
    approve_generated: bool = True


class GenerationTaskRead(BaseModel):
    task_id: str
    status: str
    scenario_ids: list[int] = Field(default_factory=list)
    created_count: int = 0
    skipped_count: int = 0
    errors: list[str] = Field(default_factory=list)
    started_at: datetime
    finished_at: datetime | None = None

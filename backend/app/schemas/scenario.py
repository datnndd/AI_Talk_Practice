from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ScenarioVariationCreate(BaseModel):
    variation_seed: str | None = Field(default=None, min_length=8, max_length=64)
    parameters: dict[str, Any] = Field(default_factory=dict)
    system_prompt_override: str | None = None
    sample_prompt: str | None = Field(default=None, max_length=500)
    is_pregenerated: bool = False
    generated_by_model: str | None = Field(default=None, max_length=100)
    generation_latency_ms: int | None = Field(default=None, ge=0)
    is_approved: bool = False


class ScenarioVariationRead(ORMModel):
    id: int
    scenario_id: int
    variation_seed: str
    parameters: dict[str, Any]
    system_prompt_override: str | None = None
    sample_prompt: str | None = None
    is_pregenerated: bool
    generated_by_model: str | None = None
    generation_latency_ms: int | None = None
    usage_count: int
    last_used_at: datetime | None = None
    is_approved: bool
    created_at: datetime
    updated_at: datetime


class ScenarioCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    learning_objectives: list[str] | str | None = Field(default_factory=list)
    ai_system_prompt: str = Field(min_length=1)
    category: str = Field(min_length=1, max_length=50)
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard)$")
    target_skills: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    estimated_duration: int | None = Field(default=None, ge=1, le=32767)
    mode: str = Field(
        default="conversation",
        pattern=r"^(conversation|roleplay|debate|interview|presentation)$",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ScenarioUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    learning_objectives: list[str] | str | None = None
    ai_system_prompt: str | None = None
    category: str | None = Field(default=None, max_length=50)
    difficulty: str | None = Field(default=None, pattern=r"^(easy|medium|hard)$")
    target_skills: list[str] | None = None
    tags: list[str] | None = None
    estimated_duration: int | None = Field(default=None, ge=1, le=32767)
    mode: str | None = Field(
        default=None,
        pattern=r"^(conversation|roleplay|debate|interview|presentation)$",
    )
    metadata: dict[str, Any] | None = None
    is_active: bool | None = None


class ScenarioRead(ORMModel):
    id: int
    title: str
    description: str
    learning_objectives: Any | None = None
    ai_system_prompt: str
    category: str
    difficulty: str
    target_skills: Any | None = None
    tags: Any | None = None
    estimated_duration: int | None = None
    mode: str
    metadata: dict[str, Any] | None = None
    is_active: bool
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime
    variations: list[ScenarioVariationRead] = Field(default_factory=list)

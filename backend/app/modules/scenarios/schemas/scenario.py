from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ScenarioCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    learning_objectives: list[str] | str | None = Field(default_factory=list)
    ai_system_prompt: str = Field(min_length=1)
    opening_message: str | None = None
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
    is_ai_start_first: bool = True


class ScenarioUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    learning_objectives: list[str] | str | None = None
    ai_system_prompt: str | None = None
    opening_message: str | None = None
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
    is_ai_start_first: bool | None = None


class ScenarioRead(ORMModel):
    id: int
    title: str
    description: str
    learning_objectives: Any | None = None
    ai_system_prompt: str
    opening_message: str | None = None
    category: str
    difficulty: str
    target_skills: Any | None = None
    tags: Any | None = None
    estimated_duration: int | None = None
    mode: str
    metadata: dict[str, Any] | None = None
    is_active: bool
    is_ai_start_first: bool
    created_by: int | None = None
    created_at: datetime
    updated_at: datetime

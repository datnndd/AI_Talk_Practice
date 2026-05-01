from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.characters.schemas import CharacterRead


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ScenarioCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1)
    ai_system_prompt: str = Field(min_length=1)
    ai_role: str = ""
    user_role: str = ""
    tasks: list[str] = Field(default_factory=list)
    category: str = Field(min_length=1, max_length=50)
    difficulty: str = Field(default="medium", pattern=r"^(easy|medium|hard)$")
    tags: list[str] = Field(default_factory=list)
    estimated_duration: int | None = Field(default=None, ge=1, le=32767)
    character_id: int | None = None
    is_active: bool = True
    is_pro: bool = False


class ScenarioUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    ai_system_prompt: str | None = None
    ai_role: str | None = None
    user_role: str | None = None
    tasks: list[str] | None = None
    category: str | None = Field(default=None, max_length=50)
    difficulty: str | None = Field(default=None, pattern=r"^(easy|medium|hard)$")
    tags: list[str] | None = None
    estimated_duration: int | None = Field(default=None, ge=1, le=32767)
    character_id: int | None = None
    is_active: bool | None = None
    is_pro: bool | None = None


class ScenarioRead(ORMModel):
    id: int
    character_id: int | None = None
    title: str
    description: str
    ai_system_prompt: str
    ai_role: str = ""
    user_role: str = ""
    image_url: str | None = None
    tasks: Any | None = None
    category: str
    difficulty: str
    tags: Any | None = None
    estimated_duration: int | None = None
    is_active: bool
    is_pro: bool
    character: CharacterRead | None = None
    created_at: datetime
    updated_at: datetime


class ScenarioListRead(ORMModel):
    id: int
    character_id: int | None = None
    title: str
    description: str
    ai_role: str = ""
    user_role: str = ""
    image_url: str | None = None
    tasks: Any | None = None
    category: str
    difficulty: str
    tags: Any | None = None
    estimated_duration: int | None = None
    is_active: bool
    is_pro: bool
    created_at: datetime
    updated_at: datetime

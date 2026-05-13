from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict

from app.modules.characters.schemas import CharacterRead


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ScenarioRead(ORMModel):
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
    time_limit_minutes: int | None = None
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
    time_limit_minutes: int | None = None
    is_active: bool
    is_pro: bool
    created_at: datetime
    updated_at: datetime

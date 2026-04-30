from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CharacterBase(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str | None = None
    model_url: str = Field(min_length=1, max_length=1000)
    core_url: str = Field(min_length=1, max_length=1000)
    thumbnail_url: str | None = Field(default=None, max_length=1000)
    tts_voice: str = Field(default="Cherry", min_length=1, max_length=100)
    tts_language: str = Field(default="en", min_length=1, max_length=20)
    is_active: bool = True
    sort_order: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class CharacterCreate(CharacterBase):
    pass


class CharacterUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = None
    model_url: str | None = Field(default=None, min_length=1, max_length=1000)
    core_url: str | None = Field(default=None, min_length=1, max_length=1000)
    thumbnail_url: str | None = Field(default=None, max_length=1000)
    tts_voice: str | None = Field(default=None, min_length=1, max_length=100)
    tts_language: str | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None
    sort_order: int | None = None
    metadata: dict[str, Any] | None = None


class CharacterRead(ORMModel):
    id: int
    name: str
    description: str | None = None
    model_url: str
    core_url: str
    thumbnail_url: str | None = None
    tts_voice: str
    tts_language: str
    is_active: bool
    sort_order: int
    metadata: dict[str, Any] = Field(default_factory=dict)
    deleted_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class CharacterListResponse(BaseModel):
    items: list[CharacterRead]
    total: int
    page: int
    page_size: int

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.characters.schemas import CharacterRead
from app.modules.scenarios.schemas import ScenarioRead


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class CorrectionCreate(BaseModel):
    original_text: str
    corrected_text: str
    explanation: str
    error_type: str = Field(
        pattern=r"^(grammar|vocabulary|naturalness|pronunciation|register)$"
    )
    severity: str = Field(default="medium", pattern=r"^(low|medium|high)$")
    position_start: int | None = Field(default=None, ge=0)
    position_end: int | None = Field(default=None, ge=0)


class CorrectionRead(ORMModel):
    id: int
    original_text: str
    corrected_text: str
    explanation: str
    error_type: str
    severity: str
    position_start: int | None = None
    position_end: int | None = None
    created_at: datetime
    updated_at: datetime


class RealtimeCorrectionItem(BaseModel):
    id: int | None = None
    original_text: str = ""
    corrected_text: str = ""
    explanation: str = ""
    error_type: str = Field(default="grammar")
    severity: str = Field(default="medium")
    position_start: int | None = Field(default=None, ge=0)
    position_end: int | None = Field(default=None, ge=0)


class SessionHintRequest(BaseModel):
    message_id: int | None = None
    text: str | None = None


class RealtimeCorrectionRequest(BaseModel):
    message_id: int | None = None
    text: str | None = None


class RealtimeCorrectionResponse(BaseModel):
    corrected_text: str
    corrections: list[RealtimeCorrectionItem] = Field(default_factory=list)
    persisted: bool = False


class MessageCreate(BaseModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(min_length=1)
    audio_url: str | None = Field(default=None, max_length=1000)
    audio_duration_ms: int | None = Field(default=None, ge=0)
    asr_metadata: Any | None = None
    corrections: list[CorrectionCreate] = Field(default_factory=list)


class MessageRead(ORMModel):
    id: int
    session_id: int
    role: str
    content: str
    order_index: int
    audio_url: str | None = None
    audio_duration_ms: int | None = None
    asr_metadata: Any | None = None
    corrections: list[CorrectionRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class SessionScoreRead(ORMModel):
    id: int
    avg_pronunciation: float
    avg_fluency: float
    avg_grammar: float
    avg_vocabulary: float
    avg_intonation: float
    relevance_score: float
    overall_score: float
    scored_message_count: int
    skill_breakdown: dict[str, Any] | None = None
    feedback_summary: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class SessionCreate(BaseModel):
    scenario_id: int
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionFinishRequest(BaseModel):
    status: str | None = Field(default=None, pattern=r"^(completed|abandoned|error)$")
    ended_at: datetime | None = None
    relevance_score: float | None = Field(default=None, ge=0, le=10)
    feedback_summary: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class SessionListItem(ORMModel):
    id: int
    scenario_id: int
    scenario_title: str
    status: str
    duration_seconds: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
    overall_score: float | None = None


class SessionRead(ORMModel):
    id: int
    user_id: int
    scenario_id: int
    character_id: int | None = None
    status: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    metadata: dict[str, Any] | None = None
    character: CharacterRead | None = None
    scenario: ScenarioRead
    messages: list[MessageRead] = Field(default_factory=list)
    score: SessionScoreRead | None = None
    created_at: datetime
    updated_at: datetime

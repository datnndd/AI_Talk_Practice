from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.scenario import ScenarioRead, ScenarioVariationRead


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


class MessageScoreCreate(BaseModel):
    pronunciation_score: float = Field(ge=0, le=10)
    fluency_score: float = Field(ge=0, le=10)
    grammar_score: float = Field(ge=0, le=10)
    vocabulary_score: float = Field(ge=0, le=10)
    intonation_score: float = Field(ge=0, le=10)
    overall_score: float = Field(ge=0, le=10)
    mispronounced_words: Any | None = None
    feedback: str | None = None
    metadata: dict[str, Any] | None = None


class MessageScoreRead(ORMModel):
    id: int
    pronunciation_score: float
    fluency_score: float
    grammar_score: float
    vocabulary_score: float
    intonation_score: float
    overall_score: float
    mispronounced_words: Any | None = None
    feedback: str | None = None
    metadata: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(min_length=1)
    audio_url: str | None = Field(default=None, max_length=1000)
    audio_duration_ms: int | None = Field(default=None, ge=0)
    asr_metadata: Any | None = None
    corrections: list[CorrectionCreate] = Field(default_factory=list)
    score: MessageScoreCreate | None = None


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
    score: MessageScoreRead | None = None
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
    variation_id: int | None = None
    variation_seed: str | None = Field(default=None, min_length=8, max_length=64)
    variation_parameters: dict[str, Any] = Field(default_factory=dict)
    prefer_pregenerated: bool = True
    create_variation_if_missing: bool = True
    mode: str | None = Field(
        default=None,
        pattern=r"^(conversation|roleplay|debate|interview|presentation)$",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
    target_skills: list[str] | None = None


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
    mode: str
    variation_id: int | None = None
    variation_seed: str | None = None
    duration_seconds: int | None = None
    started_at: datetime
    ended_at: datetime | None = None
    overall_score: float | None = None


class SessionRead(ORMModel):
    id: int
    user_id: int
    scenario_id: int
    variation_id: int | None = None
    status: str
    mode: str
    started_at: datetime
    ended_at: datetime | None = None
    duration_seconds: int | None = None
    target_skills: Any | None = None
    metadata: dict[str, Any] | None = None
    variation_seed: str | None = None
    scenario: ScenarioRead
    variation: ScenarioVariationRead | None = None
    messages: list[MessageRead] = Field(default_factory=list)
    score: SessionScoreRead | None = None
    created_at: datetime
    updated_at: datetime

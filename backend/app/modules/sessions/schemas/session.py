from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.modules.characters.schemas import CharacterRead
from app.modules.scenarios.schemas import ScenarioRead


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class MessageRealtimeFeedbackRead(ORMModel):
    id: int
    is_good: bool
    better_answer: str | None = None
    raw_response: dict[str, Any] | None = None
    created_at: datetime
    updated_at: datetime


class SessionHintRequest(BaseModel):
    pass


class RealtimeCorrectionRequest(BaseModel):
    message_id: int | None = None
    text: str | None = None


class RealtimeCorrectionResponse(BaseModel):
    is_good: bool = True
    better_answer: str | None = None
    persisted: bool = False


class MessageCreate(BaseModel):
    role: str = Field(pattern=r"^(user|assistant)$")
    content: str = Field(min_length=1)
    audio_url: str | None = Field(default=None, max_length=1000)


class MessageRead(ORMModel):
    id: int
    session_id: int
    role: str
    content: str
    order_index: int
    audio_url: str | None = None
    realtime_feedback: MessageRealtimeFeedbackRead | None = None
    created_at: datetime
    updated_at: datetime


class SessionScoreRead(ORMModel):
    id: int
    avg_fluency: float
    avg_grammar: float
    avg_vocabulary: float
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

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class PronunciationAssessmentConfigResponse(BaseModel):
    reference_text: str
    max_recording_seconds: int
    max_audio_bytes: int
    min_sample_rate: int


class PronunciationAssessmentRequest(BaseModel):
    audio_base64: str = Field(min_length=1)


class PronunciationAssessmentResponse(BaseModel):
    reference_text: str
    score: float
    source: str = "azure"
    accuracy_score: float = 0
    fluency_score: float = 0
    completeness_score: float = 0
    pronunciation_score: float = 0
    words: list[dict[str, Any]] = Field(default_factory=list)
    raw: str | None = None

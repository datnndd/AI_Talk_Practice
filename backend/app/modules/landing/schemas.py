from __future__ import annotations

from pydantic import BaseModel, Field


class FutureVoiceConfigResponse(BaseModel):
    transcript: str
    max_recording_seconds: int
    max_audio_bytes: int
    min_sample_rate: int


class FutureVoiceGenerateRequest(BaseModel):
    audio_base64: str = Field(min_length=1)
    fingerprint: str = Field(min_length=16, max_length=512)


class FutureVoiceGenerateResponse(BaseModel):
    transcript: str
    future_audio_base64: str
    content_type: str = "audio/wav"


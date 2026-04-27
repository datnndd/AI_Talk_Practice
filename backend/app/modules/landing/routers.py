from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import Response

from app.core.exceptions import NotFoundError
from app.modules.landing.schemas import (
    FutureVoiceConfigResponse,
    FutureVoiceGenerateRequest,
    FutureVoiceGenerateResponse,
)
from app.modules.landing.services import (
    FUTURE_VOICE_TRANSCRIPT,
    future_voice_config,
    generate_future_voice,
    get_temporary_audio,
)

router = APIRouter(prefix="/landing/future-voice", tags=["landing"])


@router.get("", response_model=FutureVoiceConfigResponse)
async def get_future_voice_config():
    return FutureVoiceConfigResponse(**future_voice_config())


@router.post("/generate", response_model=FutureVoiceGenerateResponse)
async def generate_future_voice_audio(body: FutureVoiceGenerateRequest):
    future_audio_base64 = await generate_future_voice(
        audio_base64=body.audio_base64,
        fingerprint=body.fingerprint,
    )
    return FutureVoiceGenerateResponse(
        transcript=FUTURE_VOICE_TRANSCRIPT,
        future_audio_base64=future_audio_base64,
    )


@router.get("/source/{token}.wav")
async def future_voice_source_audio(token: str):
    audio = await get_temporary_audio(token)
    if audio is None:
        raise NotFoundError("Temporary audio not found")
    return Response(content=audio, media_type="audio/wav")


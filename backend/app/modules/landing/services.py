from __future__ import annotations

import asyncio
import base64
import hashlib
import io
import logging
import secrets
import time
import wave
from dataclasses import dataclass
from http import HTTPStatus
from typing import Any
from urllib.parse import quote

import dashscope
import httpx

from app.core.config import Settings, settings
from app.core.exceptions import BadRequestError, ConflictError, UpstreamServiceError

logger = logging.getLogger(__name__)

FUTURE_VOICE_TRANSCRIPT = (
    "Every day I practice speaking with confidence. I listen carefully, pronounce clearly, "
    "and keep going even when a sentence feels difficult."
)

CLIENT_MAX_RECORDING_SECONDS = 20
TEMP_AUDIO_PREFIX = "fvdemo"


@dataclass(frozen=True)
class WavInfo:
    sample_rate: int
    channels: int
    sample_width: int
    frame_count: int
    duration_seconds: float


def _now() -> float:
    return time.time()


def _strip_data_url(value: str) -> str:
    if "," in value and value.split(",", 1)[0].lower().startswith("data:"):
        return value.split(",", 1)[1]
    return value


def _audio_attr(audio: Any, key: str) -> Any:
    if audio is None:
        return None
    if isinstance(audio, dict):
        return audio.get(key)
    return getattr(audio, key, None)


def _response_output(response: Any) -> Any:
    if isinstance(response, dict):
        return response.get("output")
    return getattr(response, "output", None)


def _validate_success_response(response: Any, action: str) -> None:
    status_code = getattr(response, "status_code", None)
    if status_code in (HTTPStatus.OK, 200):
        return

    code = getattr(response, "code", None) or "dashscope_error"
    message = getattr(response, "message", None) or f"DashScope {action} failed"
    raise UpstreamServiceError(message, extra={"code": code})


def decode_audio_base64(value: str, max_bytes: int) -> bytes:
    try:
        audio_bytes = base64.b64decode(_strip_data_url(value), validate=False)
    except Exception as exc:
        raise BadRequestError("Invalid audio_base64 payload") from exc

    if not audio_bytes:
        raise BadRequestError("Audio payload is empty")
    if len(audio_bytes) > max_bytes:
        raise BadRequestError("Audio payload is too large")
    return audio_bytes


def validate_wav(audio_bytes: bytes, config: Settings) -> WavInfo:
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
    except wave.Error as exc:
        raise BadRequestError("Audio must be a valid WAV file") from exc

    if channels != 1:
        raise BadRequestError("Audio must be mono WAV")
    if sample_width != 2:
        raise BadRequestError("Audio must be 16-bit PCM WAV")
    if sample_rate < config.qwen_vc_min_sample_rate:
        raise BadRequestError(f"Audio sample rate must be at least {config.qwen_vc_min_sample_rate} Hz")

    duration = frame_count / sample_rate if sample_rate else 0
    if duration <= 0:
        raise BadRequestError("Audio duration is empty")
    if duration > config.qwen_vc_max_audio_seconds:
        raise BadRequestError("Audio recording is too long")

    return WavInfo(
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
        frame_count=frame_count,
        duration_seconds=duration,
    )


class FutureVoiceTrialStore:
    def __init__(self) -> None:
        self._used: dict[str, float] = {}
        self._in_progress: set[str] = set()
        self._lock = asyncio.Lock()

    def fingerprint_hash(self, fingerprint: str, salt: str) -> str:
        normalized = fingerprint.strip()
        return hashlib.sha256(f"{salt}:{normalized}".encode("utf-8")).hexdigest()

    async def reserve(self, fingerprint_hash: str, ttl_seconds: int) -> bool:
        async with self._lock:
            self._cleanup_locked()
            if fingerprint_hash in self._in_progress:
                return False
            expires_at = self._used.get(fingerprint_hash)
            if expires_at and expires_at > _now():
                return False
            self._in_progress.add(fingerprint_hash)
            return True

    async def mark_success(self, fingerprint_hash: str, ttl_seconds: int) -> None:
        async with self._lock:
            self._in_progress.discard(fingerprint_hash)
            self._used[fingerprint_hash] = _now() + ttl_seconds
            self._cleanup_locked()

    async def release(self, fingerprint_hash: str) -> None:
        async with self._lock:
            self._in_progress.discard(fingerprint_hash)

    async def clear(self) -> None:
        async with self._lock:
            self._used.clear()
            self._in_progress.clear()

    def _cleanup_locked(self) -> None:
        now = _now()
        expired = [key for key, expires_at in self._used.items() if expires_at <= now]
        for key in expired:
            self._used.pop(key, None)


class TemporaryAudioStore:
    def __init__(self) -> None:
        self._items: dict[str, tuple[bytes, float]] = {}
        self._lock = asyncio.Lock()

    async def put(self, audio_bytes: bytes, ttl_seconds: int) -> str:
        token = secrets.token_urlsafe(24)
        async with self._lock:
            self._cleanup_locked()
            self._items[token] = (audio_bytes, _now() + ttl_seconds)
        return token

    async def get(self, token: str) -> bytes | None:
        async with self._lock:
            self._cleanup_locked()
            item = self._items.get(token)
            if not item:
                return None
            return item[0]

    async def delete(self, token: str) -> None:
        async with self._lock:
            self._items.pop(token, None)

    async def clear(self) -> None:
        async with self._lock:
            self._items.clear()

    def _cleanup_locked(self) -> None:
        now = _now()
        expired = [key for key, (_, expires_at) in self._items.items() if expires_at <= now]
        for key in expired:
            self._items.pop(key, None)


class DashScopeVoiceCloneClient:
    def __init__(self, config: Settings):
        self._config = config
        if config.dashscope_api_key:
            dashscope.api_key = config.dashscope_api_key

    async def generate(self, source_audio_url: str, transcript: str) -> bytes:
        if not self._config.dashscope_api_key:
            raise UpstreamServiceError("DashScope API key is not configured")

        voice_id: str | None = None
        try:
            voice_id = await self._run_blocking(self._create_voice, source_audio_url)
            audio = await self._run_blocking(self._synthesize_voice, voice_id, transcript)
            return await self._resolve_audio(audio)
        except UpstreamServiceError:
            raise
        except Exception as exc:
            logger.exception("Future voice generation failed")
            raise UpstreamServiceError("DashScope future voice generation failed") from exc
        finally:
            if voice_id:
                try:
                    await self._run_blocking(self._delete_voice, voice_id)
                except Exception:
                    logger.warning("Failed to delete temporary DashScope voice %s", voice_id, exc_info=True)

    async def _run_blocking(self, function, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, function, *args)

    def _create_voice(self, source_audio_url: str) -> str:
        from dashscope.audio.tts_v2 import VoiceEnrollmentService

        service = VoiceEnrollmentService(
            api_key=self._config.dashscope_api_key,
            model=self._config.qwen_vc_enrollment_model,
        )
        return service.create_voice(
            target_model=self._config.qwen_vc_target_model,
            prefix=TEMP_AUDIO_PREFIX,
            url=source_audio_url,
            language_hints=["en"],
            max_prompt_audio_length=min(10.0, self._config.qwen_vc_max_audio_seconds),
        )

    def _synthesize_voice(self, voice_id: str, transcript: str) -> Any:
        from dashscope.audio.qwen_tts import SpeechSynthesizer

        response = SpeechSynthesizer.call(
            model=self._config.qwen_vc_target_model,
            text=transcript,
            api_key=self._config.dashscope_api_key,
            voice=voice_id,
            language_type="en",
        )
        _validate_success_response(response, "synthesis")
        output = _response_output(response)
        audio = _audio_attr(output, "audio")
        if audio is None:
            raise UpstreamServiceError("DashScope synthesis response did not include audio")
        return audio

    def _delete_voice(self, voice_id: str) -> None:
        from dashscope.audio.tts_v2 import VoiceEnrollmentService

        service = VoiceEnrollmentService(
            api_key=self._config.dashscope_api_key,
            model=self._config.qwen_vc_enrollment_model,
        )
        service.delete_voice(voice_id)

    async def _resolve_audio(self, audio: Any) -> bytes:
        audio_data = _audio_attr(audio, "data")
        if audio_data:
            return base64.b64decode(audio_data)

        audio_url = _audio_attr(audio, "url")
        if not audio_url:
            raise UpstreamServiceError("DashScope synthesis response did not include audio data")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(audio_url)
            response.raise_for_status()
            return response.content


def create_voice_clone_client(config: Settings) -> DashScopeVoiceCloneClient:
    return DashScopeVoiceCloneClient(config)


trial_store = FutureVoiceTrialStore()
temporary_audio_store = TemporaryAudioStore()


def future_voice_config(config: Settings = settings) -> dict[str, int | str]:
    return {
        "transcript": FUTURE_VOICE_TRANSCRIPT,
        "max_recording_seconds": CLIENT_MAX_RECORDING_SECONDS,
        "max_audio_bytes": config.qwen_vc_max_audio_bytes,
        "min_sample_rate": config.qwen_vc_min_sample_rate,
    }


def temporary_source_url(token: str, config: Settings = settings) -> str:
    base_url = config.backend_public_url.rstrip("/")
    return f"{base_url}/api/landing/future-voice/source/{quote(token)}.wav"


async def get_temporary_audio(token: str) -> bytes | None:
    return await temporary_audio_store.get(token)


async def generate_future_voice(
    *,
    audio_base64: str,
    fingerprint: str,
    config: Settings = settings,
) -> str:
    audio_bytes = decode_audio_base64(audio_base64, config.qwen_vc_max_audio_bytes)
    validate_wav(audio_bytes, config)

    fingerprint_hash = trial_store.fingerprint_hash(fingerprint, config.qwen_vc_fingerprint_salt)
    reserved = await trial_store.reserve(fingerprint_hash, config.qwen_vc_trial_ttl_seconds)
    if not reserved:
        raise ConflictError("Future voice trial already used for this browser")

    token: str | None = None
    try:
        token = await temporary_audio_store.put(audio_bytes, config.qwen_vc_source_audio_ttl_seconds)
        source_url = temporary_source_url(token, config)
        client = create_voice_clone_client(config)
        future_audio_bytes = await client.generate(source_url, FUTURE_VOICE_TRANSCRIPT)
        if not future_audio_bytes:
            raise UpstreamServiceError("DashScope future voice generation returned empty audio")
        await trial_store.mark_success(fingerprint_hash, config.qwen_vc_trial_ttl_seconds)
        return "data:audio/wav;base64," + base64.b64encode(future_audio_bytes).decode("ascii")
    except Exception:
        await trial_store.release(fingerprint_hash)
        raise
    finally:
        if token:
            await temporary_audio_store.delete(token)


async def reset_future_voice_state() -> None:
    await trial_store.clear()
    await temporary_audio_store.clear()


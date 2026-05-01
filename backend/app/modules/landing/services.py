from __future__ import annotations

import asyncio
import base64
import io
import json
import os
import tempfile
import wave
from dataclasses import dataclass
from typing import Any

from app.core.config import Settings, settings
from app.core.exceptions import BadRequestError, UpstreamServiceError

LANDING_PRONUNCIATION_TEXT = (
    "All men have a sweetness in their life. That is what helps them go on. "
    "It is towards that they turn when they feel too worn out."
)

LANDING_PRONUNCIATION_MAX_RECORDING_SECONDS = 20
LANDING_PRONUNCIATION_MAX_AUDIO_BYTES = 10 * 1024 * 1024
LANDING_PRONUNCIATION_MAX_AUDIO_SECONDS = 60.0
LANDING_PRONUNCIATION_MIN_SAMPLE_RATE = 16000


@dataclass(frozen=True)
class WavInfo:
    sample_rate: int
    channels: int
    sample_width: int
    frame_count: int
    duration_seconds: float


def _strip_data_url(value: str) -> str:
    if "," in value and value.split(",", 1)[0].lower().startswith("data:"):
        return value.split(",", 1)[1]
    return value


def decode_audio_base64(value: str, max_bytes: int = LANDING_PRONUNCIATION_MAX_AUDIO_BYTES) -> bytes:
    try:
        audio_bytes = base64.b64decode(_strip_data_url(value), validate=False)
    except Exception as exc:
        raise BadRequestError("Invalid audio_base64 payload") from exc

    if not audio_bytes:
        raise BadRequestError("Audio payload is empty")
    if len(audio_bytes) > max_bytes:
        raise BadRequestError("Audio payload is too large")
    return audio_bytes


def validate_wav(audio_bytes: bytes) -> WavInfo:
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
    if sample_rate < LANDING_PRONUNCIATION_MIN_SAMPLE_RATE:
        raise BadRequestError(f"Audio sample rate must be at least {LANDING_PRONUNCIATION_MIN_SAMPLE_RATE} Hz")

    duration = frame_count / sample_rate if sample_rate else 0
    if duration <= 0:
        raise BadRequestError("Audio duration is empty")
    if duration > LANDING_PRONUNCIATION_MAX_AUDIO_SECONDS:
        raise BadRequestError("Audio recording is too long")

    return WavInfo(
        sample_rate=sample_rate,
        channels=channels,
        sample_width=sample_width,
        frame_count=frame_count,
        duration_seconds=duration,
    )


def _json_words(json_result: str) -> list[dict[str, Any]]:
    try:
        payload = json.loads(json_result)
    except json.JSONDecodeError:
        return []
    words = payload.get("NBest", [{}])[0].get("Words", [])
    return words if isinstance(words, list) else []


class AzurePronunciationAssessmentClient:
    def __init__(self, config: Settings):
        self._config = config

    async def assess(self, *, audio_bytes: bytes, reference_text: str) -> dict[str, Any]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, self._assess_sync, audio_bytes, reference_text)

    def _assess_sync(self, audio_bytes: bytes, reference_text: str) -> dict[str, Any]:
        if not self._config.azure_speech_key or not self._config.azure_speech_region:
            raise UpstreamServiceError("Azure Speech is not configured")

        try:
            import azure.cognitiveservices.speech as speechsdk
        except Exception as exc:
            raise UpstreamServiceError("Azure Speech SDK is not installed") from exc

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            speech_config = speechsdk.SpeechConfig(
                subscription=self._config.azure_speech_key,
                region=self._config.azure_speech_region,
            )
            speech_config.speech_recognition_language = self._config.azure_speech_language or "en-US"
            audio_config = speechsdk.AudioConfig(filename=temp_path)
            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                enable_miscue=True,
            )
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            pronunciation_config.apply_to(recognizer)
            result = recognizer.recognize_once()
            if result.reason == speechsdk.ResultReason.Canceled:
                details = speechsdk.CancellationDetails(result)
                raise UpstreamServiceError(f"Azure pronunciation assessment canceled: {details.reason}")

            assessment = speechsdk.PronunciationAssessmentResult(result)
            json_result = result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult,
                "{}",
            )
            score = float(assessment.pronunciation_score or assessment.accuracy_score or 0)
            return {
                "score": round(score, 2),
                "source": "azure",
                "accuracy_score": round(float(assessment.accuracy_score or 0), 2),
                "fluency_score": round(float(assessment.fluency_score or 0), 2),
                "completeness_score": round(float(assessment.completeness_score or 0), 2),
                "pronunciation_score": round(float(assessment.pronunciation_score or 0), 2),
                "words": _json_words(json_result),
                "raw": json_result,
            }
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass


def create_pronunciation_assessment_client(config: Settings) -> AzurePronunciationAssessmentClient:
    return AzurePronunciationAssessmentClient(config)


def pronunciation_assessment_config() -> dict[str, int | str]:
    return {
        "reference_text": LANDING_PRONUNCIATION_TEXT,
        "max_recording_seconds": LANDING_PRONUNCIATION_MAX_RECORDING_SECONDS,
        "max_audio_bytes": LANDING_PRONUNCIATION_MAX_AUDIO_BYTES,
        "min_sample_rate": LANDING_PRONUNCIATION_MIN_SAMPLE_RATE,
    }


async def assess_landing_pronunciation(
    *,
    audio_base64: str,
    config: Settings = settings,
) -> dict[str, Any]:
    audio_bytes = decode_audio_base64(audio_base64, LANDING_PRONUNCIATION_MAX_AUDIO_BYTES)
    validate_wav(audio_bytes)
    client = create_pronunciation_assessment_client(config)
    return await client.assess(audio_bytes=audio_bytes, reference_text=LANDING_PRONUNCIATION_TEXT)

import base64
import io
import wave

import pytest

from app.core.exceptions import UpstreamServiceError
from app.modules.landing import services as landing_services
from app.modules.landing.services import LANDING_PRONUNCIATION_TEXT


def make_wav_data_url(sample_rate=24000, seconds=1.0):
    frame_count = int(sample_rate * seconds)
    audio = io.BytesIO()
    with wave.open(audio, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(b"\x00\x00" * frame_count)
    encoded = base64.b64encode(audio.getvalue()).decode("ascii")
    return f"data:audio/wav;base64,{encoded}"


@pytest.mark.asyncio
async def test_pronunciation_assessment_config_is_public(client):
    response = await client.get("/api/landing/pronunciation-assessment")

    assert response.status_code == 200
    data = response.json()
    assert data["reference_text"] == LANDING_PRONUNCIATION_TEXT
    assert data["max_recording_seconds"] == 20
    assert data["min_sample_rate"] == 16000


@pytest.mark.asyncio
async def test_pronunciation_assessment_rejects_invalid_wav(client):
    payload = {
        "audio_base64": base64.b64encode(b"not a wav").decode("ascii"),
    }

    response = await client.post("/api/landing/pronunciation-assessment/score", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"


@pytest.mark.asyncio
async def test_pronunciation_assessment_rejects_too_large_audio(client, monkeypatch):
    monkeypatch.setattr(landing_services, "LANDING_PRONUNCIATION_MAX_AUDIO_BYTES", 16)
    payload = {
        "audio_base64": base64.b64encode(b"x" * 17).decode("ascii"),
    }

    response = await client.post("/api/landing/pronunciation-assessment/score", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Audio payload is too large"


@pytest.mark.asyncio
async def test_pronunciation_assessment_scores_with_azure_client(client, monkeypatch):
    calls = []

    class FakeAssessmentClient:
        async def assess(self, *, audio_bytes, reference_text):
            calls.append((len(audio_bytes), reference_text))
            return {
                "score": 88.5,
                "source": "azure",
                "accuracy_score": 91.0,
                "fluency_score": 82.0,
                "completeness_score": 97.0,
                "pronunciation_score": 88.5,
                "words": [{"Word": "Every", "PronunciationAssessment": {"AccuracyScore": 90}}],
                "raw": "{}",
            }

    monkeypatch.setattr(
        landing_services,
        "create_pronunciation_assessment_client",
        lambda _config: FakeAssessmentClient(),
    )

    response = await client.post(
        "/api/landing/pronunciation-assessment/score",
        json={"audio_base64": make_wav_data_url()},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["reference_text"] == LANDING_PRONUNCIATION_TEXT
    assert data["score"] == 88.5
    assert data["source"] == "azure"
    assert data["accuracy_score"] == 91.0
    assert data["words"][0]["Word"] == "Every"
    assert calls[0][1] == LANDING_PRONUNCIATION_TEXT


@pytest.mark.asyncio
async def test_pronunciation_assessment_azure_failure_returns_502(client, monkeypatch):
    class FailingAssessmentClient:
        async def assess(self, *, audio_bytes, reference_text):
            raise UpstreamServiceError("Azure Speech is not configured")

    monkeypatch.setattr(
        landing_services,
        "create_pronunciation_assessment_client",
        lambda _config: FailingAssessmentClient(),
    )

    response = await client.post(
        "/api/landing/pronunciation-assessment/score",
        json={"audio_base64": make_wav_data_url()},
    )

    assert response.status_code == 502
    assert response.json()["detail"] == "Azure Speech is not configured"

import base64
import io
import wave

import pytest
import pytest_asyncio

from app.core.exceptions import UpstreamServiceError
from app.modules.landing import services as landing_services
from app.modules.landing.services import FUTURE_VOICE_TRANSCRIPT, reset_future_voice_state


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


@pytest_asyncio.fixture(autouse=True)
async def clear_future_voice_state():
    await reset_future_voice_state()
    yield
    await reset_future_voice_state()


@pytest.mark.asyncio
async def test_future_voice_config_is_public(client):
    response = await client.get("/api/landing/future-voice")

    assert response.status_code == 200
    data = response.json()
    assert data["transcript"] == FUTURE_VOICE_TRANSCRIPT
    assert data["max_recording_seconds"] == 20
    assert data["min_sample_rate"] == 24000


@pytest.mark.asyncio
async def test_future_voice_rejects_invalid_wav(client):
    payload = {
        "audio_base64": base64.b64encode(b"not a wav").decode("ascii"),
        "fingerprint": "invalid-wav-fingerprint",
    }

    response = await client.post("/api/landing/future-voice/generate", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "bad_request"


@pytest.mark.asyncio
async def test_future_voice_rejects_too_large_audio(client, monkeypatch):
    monkeypatch.setattr(landing_services.settings, "qwen_vc_max_audio_bytes", 16)
    payload = {
        "audio_base64": base64.b64encode(b"x" * 17).decode("ascii"),
        "fingerprint": "too-large-fingerprint",
    }

    response = await client.post("/api/landing/future-voice/generate", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == "Audio payload is too large"


@pytest.mark.asyncio
async def test_future_voice_generation_marks_trial_used(client, monkeypatch):
    calls = []

    class FakeVoiceCloneClient:
        async def generate(self, source_audio_url, transcript):
            calls.append((source_audio_url, transcript))
            return b"future-wav-bytes"

    monkeypatch.setattr(
        landing_services,
        "create_voice_clone_client",
        lambda _config: FakeVoiceCloneClient(),
    )

    payload = {
        "audio_base64": make_wav_data_url(),
        "fingerprint": "success-fingerprint-123",
    }

    first = await client.post("/api/landing/future-voice/generate", json=payload)
    second = await client.post("/api/landing/future-voice/generate", json=payload)

    assert first.status_code == 200
    first_data = first.json()
    assert first_data["transcript"] == FUTURE_VOICE_TRANSCRIPT
    assert first_data["future_audio_base64"].startswith("data:audio/wav;base64,")
    assert base64.b64decode(first_data["future_audio_base64"].split(",", 1)[1]) == b"future-wav-bytes"
    assert second.status_code == 409
    assert calls[0][0].endswith(".wav")
    assert calls[0][1] == FUTURE_VOICE_TRANSCRIPT


@pytest.mark.asyncio
async def test_future_voice_upstream_failure_does_not_consume_trial(client, monkeypatch):
    class FailingVoiceCloneClient:
        async def generate(self, source_audio_url, transcript):
            raise UpstreamServiceError("DashScope failed")

    class SuccessfulVoiceCloneClient:
        async def generate(self, source_audio_url, transcript):
            return b"future-wav-bytes"

    monkeypatch.setattr(
        landing_services,
        "create_voice_clone_client",
        lambda _config: FailingVoiceCloneClient(),
    )

    payload = {
        "audio_base64": make_wav_data_url(),
        "fingerprint": "retry-fingerprint-123",
    }

    first = await client.post("/api/landing/future-voice/generate", json=payload)
    assert first.status_code == 502

    monkeypatch.setattr(
        landing_services,
        "create_voice_clone_client",
        lambda _config: SuccessfulVoiceCloneClient(),
    )
    second = await client.post("/api/landing/future-voice/generate", json=payload)

    assert second.status_code == 200

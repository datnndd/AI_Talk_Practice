import pytest
from urllib.parse import parse_qs, urlparse

from app.core.config import Settings
import app.infra.asr.deepgram_asr as deepgram_asr_module
from app.infra.asr.deepgram_asr import DeepgramASR
from app.infra.factory import create_asr


def test_create_asr_uses_deepgram_by_default():
    asr = create_asr(Settings(_env_file=None))
    assert isinstance(asr, DeepgramASR)
    assert asr._config.deepgram_asr_model == "flux-general-en"


def test_create_asr_rejects_removed_dashscope_provider():
    with pytest.raises(ValueError, match="Available: deepgram"):
        create_asr(Settings(asr_provider="dashscope"))


class FakeDeepgramWebSocket:
    async def send(self, _message):
        return None

    async def close(self):
        return None

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise StopAsyncIteration


@pytest.mark.asyncio
async def test_deepgram_asr_uses_flux_v2_url_and_query(monkeypatch):
    captured = {}

    async def fake_connect(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return FakeDeepgramWebSocket()

    monkeypatch.setattr(deepgram_asr_module, "connect", fake_connect)

    asr = DeepgramASR(Settings(_env_file=None, deepgram_api_key="test-key"))
    await asr.start_session(language="en", sample_rate=16000)
    await asr.close()

    parsed = urlparse(captured["url"])
    query = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "wss://api.deepgram.com/v2/listen"
    assert query["model"] == ["flux-general-en"]
    assert query["language"] == ["en"]
    assert query["encoding"] == ["linear16"]
    assert query["sample_rate"] == ["16000"]
    assert query["eot_threshold"] == ["0.7"]
    assert query["eot_timeout_ms"] == ["1200"]
    assert "endpointing" not in query
    assert "utterance_end_ms" not in query


def test_deepgram_asr_maps_flux_turn_info_events():
    asr = DeepgramASR(Settings(_env_file=None))

    asr._handle_payload({"type": "TurnInfo", "event": "Update", "transcript": "hello"})
    partial = asr._drain_transcript_queue()
    assert partial is not None
    assert partial.text == "hello"
    assert partial.type.value == "partial"

    asr._handle_payload({"type": "TurnInfo", "event": "EndOfTurn", "transcript": "hello there"})
    final = asr._drain_transcript_queue()
    assert final is not None
    assert final.text == "hello there"
    assert final.type.value == "final"

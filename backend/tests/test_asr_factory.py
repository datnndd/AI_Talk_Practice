import asyncio
from urllib.parse import parse_qs, urlparse

import pytest

from app.core.config import Settings
import app.infra.asr.deepgram_asr as deepgram_asr_module
from app.infra.asr.deepgram_asr import DeepgramASR
from app.infra.factory import create_asr

def test_create_asr_uses_deepgram_by_default():
    asr = create_asr(Settings(_env_file=None, deepgram_asr_model="nova-3"))
    assert isinstance(asr, DeepgramASR)
    assert asr._config.deepgram_asr_model == "nova-3"

def test_create_asr_rejects_removed_dashscope_provider():
    with pytest.raises(ValueError, match="Available: deepgram"):
        create_asr(Settings(asr_provider="dashscope"))

class FakeDeepgramWebSocket:
    messages = []

    def __init__(self):
        self.sent = []
        self._messages = list(self.messages)

    async def send(self, _message):
        self.sent.append(_message)
        return None

    async def close(self):
        return None

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self._messages:
            return self._messages.pop(0)
        raise StopAsyncIteration

@pytest.mark.asyncio
async def test_deepgram_asr_uses_nova_v1_url_and_query(monkeypatch):
    captured = {}
    fake_websocket = FakeDeepgramWebSocket()

    async def fake_connect(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return fake_websocket

    monkeypatch.setattr(deepgram_asr_module, "connect", fake_connect)

    asr = DeepgramASR(
        Settings(
            _env_file=None,
            deepgram_api_key="test-key",
            deepgram_asr_model="nova-3",
            deepgram_ws_url="wss://api.deepgram.com/v1/listen",
            deepgram_endpointing_ms=800,
        )
    )
    await asr.start_session(language="en", sample_rate=16000)
    await asr.close()

    parsed = urlparse(captured["url"])
    query = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == "wss://api.deepgram.com/v1/listen"
    assert query["model"] == ["nova-3"]
    assert query["language"] == ["en"]
    assert query["encoding"] == ["linear16"]
    assert query["sample_rate"] == ["16000"]
    assert query["channels"] == ["1"]
    assert query["smart_format"] == ["true"]
    assert query["interim_results"] == ["false"]
    assert "utterance_end_ms" not in query
    assert query["endpointing"] == ["800"]
    assert "eot_threshold" not in query
    assert "eot_timeout_ms" not in query

@pytest.mark.asyncio
async def test_deepgram_asr_sends_utterance_end_ms_when_interim_results_enabled(monkeypatch):
    captured = {}
    fake_websocket = FakeDeepgramWebSocket()

    async def fake_connect(url, **kwargs):
        captured["url"] = url
        captured["kwargs"] = kwargs
        return fake_websocket

    monkeypatch.setattr(deepgram_asr_module, "connect", fake_connect)

    asr = DeepgramASR(
        Settings(
            _env_file=None,
            deepgram_api_key="test-key",
            deepgram_interim_results=True,
            deepgram_utterance_end_ms=1000,
        )
    )
    await asr.start_session(language="en", sample_rate=16000)
    await asr.close()

    query = parse_qs(urlparse(captured["url"]).query)
    assert query["interim_results"] == ["true"]
    assert query["utterance_end_ms"] == ["1000"]

@pytest.mark.asyncio
async def test_deepgram_asr_finalizes_before_closing(monkeypatch):
    fake_websocket = FakeDeepgramWebSocket()

    async def fake_connect(_url, **_kwargs):
        return fake_websocket

    monkeypatch.setattr(deepgram_asr_module, "connect", fake_connect)

    asr = DeepgramASR(Settings(_env_file=None, deepgram_api_key="test-key"))
    await asr.start_session(language="en", sample_rate=16000)
    await asr.stop_session()

    assert '{"type": "Finalize"}' in fake_websocket.sent
    assert '{"type": "CloseStream"}' in fake_websocket.sent

@pytest.mark.asyncio
async def test_deepgram_asr_logs_raw_payloads(monkeypatch, tmp_path):
    fake_websocket = FakeDeepgramWebSocket()
    fake_websocket._messages = [
        '{"type":"Results","channel":{"alternatives":[{"transcript":"hello"}]},"is_final":true}'
    ]
    log_file = tmp_path / "deepgram_asr.log"

    async def fake_connect(_url, **_kwargs):
        return fake_websocket

    monkeypatch.setattr(deepgram_asr_module, "connect", fake_connect)

    asr = DeepgramASR(
        Settings(
            _env_file=None,
            deepgram_api_key="test-key",
            deepgram_log_payloads=True,
            deepgram_log_file=str(log_file),
        )
    )
    await asr.start_session(language="en", sample_rate=16000)
    await asyncio.sleep(0)
    await asr.stop_session()

    log_text = log_file.read_text(encoding="utf-8")
    assert "Deepgram ASR session started" in log_text
    assert "Deepgram raw response:" in log_text
    assert '"transcript":"hello"' in log_text

def test_deepgram_asr_maps_nova_partial_result():
    asr = DeepgramASR(Settings(_env_file=None))

    asr._handle_payload(
        {
            "type": "Results",
            "channel": {"alternatives": [{"transcript": "hello"}]},
            "is_final": False,
        }
    )

    event = asr._drain_transcript_queue()
    assert event is not None
    assert event.text == "hello"
    assert event.type.value == "partial"

def test_deepgram_asr_maps_nova_final_result():
    asr = DeepgramASR(Settings(_env_file=None))

    asr._handle_payload(
        {
            "type": "Results",
            "channel": {"alternatives": [{"transcript": "hello there"}]},
            "is_final": True,
        }
    )

    event = asr._drain_transcript_queue()
    assert event is not None
    assert event.text == "hello there"
    assert event.type.value == "final"

def test_deepgram_asr_merges_overlapping_final_segments():
    asr = DeepgramASR(Settings(_env_file=None))

    asr._handle_payload(
        {
            "type": "Results",
            "channel": {"alternatives": [{"transcript": "I want to book a"}]},
            "is_final": True,
        }
    )
    asr._handle_payload(
        {
            "type": "Results",
            "channel": {"alternatives": [{"transcript": "book a table for two"}]},
            "is_final": True,
        }
    )

    event = asr._drain_transcript_queue()
    assert event is not None
    assert event.text == "I want to book a table for two"
    assert event.type.value == "final"

def test_deepgram_asr_maps_speech_final_to_speech_end():
    asr = DeepgramASR(Settings(_env_file=None))

    asr._handle_payload(
        {
            "type": "Results",
            "channel": {"alternatives": [{"transcript": "hello there"}]},
            "is_final": True,
            "speech_final": True,
        }
    )

    first = asr._transcript_queue.get_nowait()
    second = asr._transcript_queue.get_nowait()
    assert first.text == "hello there"
    assert first.type.value == "final"
    assert second.text == ""
    assert second.type.value == "speech_end"

def test_deepgram_asr_ignores_utterance_end_when_interim_results_disabled():
    asr = DeepgramASR(Settings(_env_file=None))

    asr._handle_payload({"type": "UtteranceEnd", "last_word_end": 1.2})

    assert asr._drain_transcript_queue() is None

def test_deepgram_asr_maps_utterance_end_when_interim_results_enabled():
    asr = DeepgramASR(Settings(_env_file=None, deepgram_interim_results=True))

    asr._handle_payload({"type": "UtteranceEnd", "last_word_end": 1.2})

    event = asr._drain_transcript_queue()
    assert event is not None
    assert event.text == ""
    assert event.type.value == "speech_end"

def test_deepgram_asr_ignores_empty_utterance_end():
    asr = DeepgramASR(Settings(_env_file=None))

    asr._handle_payload({"type": "UtteranceEnd", "last_word_end": -1})

    assert asr._drain_transcript_queue() is None

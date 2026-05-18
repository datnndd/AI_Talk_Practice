import base64
from http import HTTPStatus
from types import SimpleNamespace

import pytest

from app.core.config import Settings
from app.infra.contracts import TTSConfig
from app.infra.tts import dashscope_tts as dashscope_tts_module


@pytest.mark.asyncio
async def test_dashscope_tts_streams_decoded_audio(monkeypatch):
    calls = []

    def fake_call(**kwargs):
        calls.append(kwargs)
        audio = base64.b64encode(b"pcm-bytes").decode("ascii")
        return iter(
            [
                SimpleNamespace(
                    status_code=HTTPStatus.OK,
                    output={"audio": {"data": audio}},
                    code=None,
                    message=None,
                    request_id="req_test",
                )
            ]
        )

    async def run_inline(_self, function, *args):
        return function(*args)

    monkeypatch.setattr(dashscope_tts_module.MultiModalConversation, "call", fake_call)
    monkeypatch.setattr(dashscope_tts_module.DashScopeTTS, "_run_blocking", run_inline)

    tts = dashscope_tts_module.DashScopeTTS(Settings(tts_model="qwen3-tts-flash"))

    async def text_stream():
        yield "Hello "
        yield "there."

    chunks = []
    async for chunk in tts.synthesize_stream(
        text_stream(),
        config=TTSConfig(
            voice="Cherry",
            language="en",
            instructions="Ignored for non-realtime TTS.",
        ),
    ):
        chunks.append(chunk)

    assert chunks == [b"pcm-bytes"]
    assert calls == [
        {
            "model": "qwen3-tts-flash",
            "text": "Hello there.",
            "voice": "Cherry",
            "stream": True,
            "result_format": "pcm",
            "sample_rate": 24000,
            "language_type": "English",
        }
    ]


@pytest.mark.asyncio
async def test_dashscope_tts_logs_api_errors_without_audio(monkeypatch, caplog):
    def fake_call(**kwargs):
        return iter(
            [
                SimpleNamespace(
                    status_code=400,
                    output=None,
                    code="InvalidParameter",
                    message="bad voice",
                    request_id="req_bad",
                )
            ]
        )

    async def run_inline(_self, function, *args):
        return function(*args)

    monkeypatch.setattr(dashscope_tts_module.MultiModalConversation, "call", fake_call)
    monkeypatch.setattr(dashscope_tts_module.DashScopeTTS, "_run_blocking", run_inline)

    tts = dashscope_tts_module.DashScopeTTS(Settings(tts_model="qwen3-tts-flash"))

    async def text_stream():
        yield "Hello there."

    chunks = []
    with caplog.at_level("ERROR"):
        async for chunk in tts.synthesize_stream(text_stream(), config=TTSConfig(voice="Cherry", language="en")):
            chunks.append(chunk)

    assert chunks == []
    assert "DashScope TTS error" in caplog.text
    assert "InvalidParameter" in caplog.text
    assert "req_bad" in caplog.text


@pytest.mark.asyncio
async def test_dashscope_tts_empty_text_skips_api_call(monkeypatch):
    called = False

    def fake_call(**kwargs):
        nonlocal called
        called = True
        return iter([])

    monkeypatch.setattr(dashscope_tts_module.MultiModalConversation, "call", fake_call)
    tts = dashscope_tts_module.DashScopeTTS(Settings(tts_model="qwen3-tts-flash"))

    async def text_stream():
        yield "   "

    chunks = []
    async for chunk in tts.synthesize_stream(text_stream(), config=TTSConfig()):
        chunks.append(chunk)

    assert chunks == []
    assert called is False

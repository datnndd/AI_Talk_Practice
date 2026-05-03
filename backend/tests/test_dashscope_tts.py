import base64

import pytest

from app.core.config import Settings
from app.infra.contracts import TTSConfig
from app.infra.tts import dashscope_tts as dashscope_tts_module
from app.infra.tts.dashscope_tts import _SafeQwenTtsRealtime


class CapturingCallback:
    def __init__(self):
        self.closed = []
        self.events = []

    def on_open(self):
        return None

    def on_close(self, close_status_code, close_msg):
        self.closed.append((close_status_code, close_msg))

    def on_event(self, message):
        self.events.append(message)


class FakeRealtimeClient:
    instances = []

    def __init__(self, model, callback, url, **kwargs):
        self.model = model
        self.callback = callback
        self.url = url
        self.kwargs = kwargs
        self.calls = []
        self.last_message = {"type": "session.created"}
        self.last_response_id = "resp_test"
        FakeRealtimeClient.instances.append(self)

    def connect(self):
        self.calls.append(("connect",))

    def update_session(self, **kwargs):
        self.calls.append(("update_session", kwargs))

    def append_text(self, text):
        self.calls.append(("append_text", text))

    def commit(self):
        self.calls.append(("commit",))
        payload = base64.b64encode(b"pcm-bytes").decode("ascii")
        self.callback.on_event({"type": "response.audio.delta", "delta": payload})
        self.callback.on_event({"type": "response.done"})

    def finish(self):
        self.calls.append(("finish",))
        self.callback.on_event({"type": "session.finished"})

    def close(self):
        self.calls.append(("close",))

    def get_last_message(self):
        return self.last_message

    def get_last_response_id(self):
        return self.last_response_id


@pytest.mark.asyncio
async def test_dashscope_tts_commits_and_yields_audio(monkeypatch):
    FakeRealtimeClient.instances.clear()
    monkeypatch.setattr(dashscope_tts_module, "_SafeQwenTtsRealtime", FakeRealtimeClient)

    async def run_inline(_self, function, *args):
        return function(*args)

    monkeypatch.setattr(dashscope_tts_module.DashScopeTTS, "_run_blocking", run_inline)

    tts = dashscope_tts_module.DashScopeTTS(Settings())

    async def text_stream():
        yield "Hello there."

    chunks = []
    async for chunk in tts.synthesize_stream(text_stream(), config=TTSConfig(voice="myvoice", language="en")):
        chunks.append(chunk)

    assert chunks == [b"pcm-bytes"]
    client = FakeRealtimeClient.instances[0]
    assert client.model == "qwen3-tts-instruct-flash-realtime-2026-01-22"
    assert (
        "update_session",
        {
            "voice": "myvoice",
            "response_format": dashscope_tts_module.AudioFormat.PCM_24000HZ_MONO_16BIT,
            "mode": "commit",
            "language_type": "en",
            "instructions": "Speak in a natural, friendly English tutor voice with clear pronunciation.",
            "enable_instructions_optimization": True,
        },
    ) in client.calls
    assert ("connect",) in client.calls
    assert ("commit",) in client.calls
    assert ("finish",) not in client.calls
    assert ("close",) in client.calls


@pytest.mark.asyncio
async def test_dashscope_tts_uses_configured_model(monkeypatch):
    FakeRealtimeClient.instances.clear()
    monkeypatch.setattr(dashscope_tts_module, "_SafeQwenTtsRealtime", FakeRealtimeClient)

    async def run_inline(_self, function, *args):
        return function(*args)

    monkeypatch.setattr(dashscope_tts_module.DashScopeTTS, "_run_blocking", run_inline)

    tts = dashscope_tts_module.DashScopeTTS(
        Settings(tts_model="qwen3-tts-vc-realtime-2025-12-01")
    )

    async def text_stream():
        yield "Hello there."

    chunks = []
    async for chunk in tts.synthesize_stream(text_stream(), config=TTSConfig(voice="myvoice", language="en")):
        chunks.append(chunk)

    assert chunks == [b"pcm-bytes"]
    assert FakeRealtimeClient.instances[0].model == "qwen3-tts-vc-realtime-2025-12-01"


def test_dashscope_tts_invalid_close_frame_is_treated_as_close():
    callback = CapturingCallback()
    client = _SafeQwenTtsRealtime(
        model="qwen3-tts-flash-realtime",
        callback=callback,
        url="wss://example.invalid/realtime",
    )

    client.on_error(None, Exception("Invalid close frame."))

    assert callback.closed == [(None, "Invalid close frame.")]
    assert callback.events == []


def test_dashscope_tts_websocket_error_is_reported_as_error_event():
    callback = CapturingCallback()
    client = _SafeQwenTtsRealtime(
        model="qwen3-tts-flash-realtime",
        callback=callback,
        url="wss://example.invalid/realtime",
    )

    client.on_error(None, Exception("network down"))

    assert callback.closed == []
    assert callback.events == [
        {
            "type": "error",
            "error": {"message": "network down"},
        }
    ]

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

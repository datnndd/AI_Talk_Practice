"""
DashScope Realtime TTS provider.

Uses Alibaba Cloud's DashScope QwenTtsRealtime for real-time
text-to-speech via WebSocket (model: qwen3-tts-flash-realtime).
"""

import asyncio
import base64
import logging
import threading
from typing import AsyncGenerator, Optional

import dashscope
from dashscope.audio.qwen_tts_realtime import (
    AudioFormat,
    QwenTtsRealtime,
    QwenTtsRealtimeCallback,
)

from app.core.config import Settings
from app.infra.contracts import TTSBase, TTSConfig

logger = logging.getLogger(__name__)


class _TTSCallback(QwenTtsRealtimeCallback):
    """Callback handler for DashScope realtime TTS events."""

    def __init__(self, audio_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self._queue = audio_queue
        self._loop = loop
        self._done_event = threading.Event()
        self._sentinel_emitted = False

    def on_open(self) -> None:
        logger.info("DashScope TTS: connection opened")

    def on_close(self, close_status_code, close_msg) -> None:
        logger.info(f"DashScope TTS: connection closed (code={close_status_code})")
        if not self._sentinel_emitted:
            self._sentinel_emitted = True
            self._loop.call_soon_threadsafe(self._queue.put_nowait, None)
        self._done_event.set()

    def on_event(self, response: dict) -> None:
        event_type = response.get("type", "")

        if event_type == "response.audio.delta":
            audio_b64 = response.get("delta", "")
            if audio_b64:
                audio_bytes = base64.b64decode(audio_b64)
                self._loop.call_soon_threadsafe(self._queue.put_nowait, audio_bytes)

        elif event_type == "response.done":
            logger.debug("DashScope TTS: response done")

        elif event_type == "session.finished":
            logger.debug("DashScope TTS: session finished")
            # Signal end of audio with None sentinel
            if not self._sentinel_emitted:
                self._sentinel_emitted = True
                self._loop.call_soon_threadsafe(self._queue.put_nowait, None)
            self._done_event.set()

        elif event_type == "error":
            error_msg = response.get("error", {}).get("message", "Unknown error")
            logger.error(f"DashScope TTS error: {error_msg}")
            if not self._sentinel_emitted:
                self._sentinel_emitted = True
                self._loop.call_soon_threadsafe(self._queue.put_nowait, None)
            self._done_event.set()

    def wait_for_done(self, timeout: float = 30.0):
        self._done_event.wait(timeout=timeout)


class DashScopeTTS(TTSBase):
    """DashScope Realtime TTS using qwen3-tts-flash-realtime."""

    def __init__(self, config: Settings):
        self._config = config

        # Set API key
        if config.dashscope_api_key:
            dashscope.api_key = config.dashscope_api_key

    async def synthesize_stream(
        self,
        text_iterator: AsyncGenerator[str, None],
        config: Optional[TTSConfig] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Convert streamed text into streamed audio."""
        cfg = config or TTSConfig(
            voice=self._config.tts_voice,
            language=self._config.tts_language,
        )

        loop = asyncio.get_event_loop()
        audio_queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue()
        callback = _TTSCallback(audio_queue, loop)

        tts_client = QwenTtsRealtime(
            model="qwen3-tts-flash-realtime",
            callback=callback,
            url=self._config.dashscope_ws_url,
        )

        # Connect and configure in executor
        await loop.run_in_executor(None, tts_client.connect)
        await loop.run_in_executor(
            None,
            lambda: tts_client.update_session(
                voice=cfg.voice,
                response_format=AudioFormat.PCM_24000HZ_MONO_16BIT,
                mode="server_commit",
            ),
        )

        # Send text chunks in background task
        async def _send_text():
            try:
                async for text_chunk in text_iterator:
                    if text_chunk.strip():
                        await loop.run_in_executor(
                            None, tts_client.append_text, text_chunk
                        )
                        await asyncio.sleep(0.05)  # Small delay between chunks
            except Exception as e:
                logger.error(f"Error sending text to TTS: {e}")
            finally:
                await loop.run_in_executor(None, tts_client.finish)

        send_task = asyncio.create_task(_send_text())

        # Yield audio chunks as they arrive
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(audio_queue.get(), timeout=30.0)
                    if chunk is None:  # Sentinel: end of audio
                        break
                    yield chunk
                except asyncio.TimeoutError:
                    logger.warning("TTS audio queue timeout")
                    break
        finally:
            if not send_task.done():
                send_task.cancel()
                try:
                    await send_task
                except asyncio.CancelledError:
                    pass
            await loop.run_in_executor(None, callback.wait_for_done, 5.0)
            try:
                await loop.run_in_executor(None, tts_client.close)
            except Exception as e:
                logger.debug(f"DashScope TTS close ignored: {e}")

    async def synthesize(
        self,
        text: str,
        config: Optional[TTSConfig] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Synthesize complete text to streamed audio."""

        async def _text_gen():
            yield text

        async for chunk in self.synthesize_stream(_text_gen(), config):
            yield chunk

    async def close(self) -> None:
        """Clean up resources."""
        pass

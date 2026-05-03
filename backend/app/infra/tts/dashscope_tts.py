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
        if self._done_event.is_set():
            logger.debug("DashScope TTS: duplicate close ignored (code=%s)", close_status_code)
            return

        logger.info(f"DashScope TTS: connection closed (code={close_status_code})")
        if not self._sentinel_emitted:
            self._sentinel_emitted = True
            self._loop.call_soon_threadsafe(self._queue.put_nowait, None)
        self._done_event.set()

    def on_event(self, response: dict) -> None:
        event_type = response.get("type", "")
        logger.debug("DashScope TTS event: %s", event_type)

        if event_type == "response.audio.delta":
            audio_b64 = response.get("delta", "")
            if audio_b64:
                try:
                    audio_bytes = base64.b64decode(audio_b64)
                except Exception:
                    logger.exception("DashScope TTS: failed to decode audio delta")
                else:
                    self._loop.call_soon_threadsafe(self._queue.put_nowait, audio_bytes)

        elif event_type == "response.done":
            logger.info("DashScope TTS: response done")
            if not self._sentinel_emitted:
                self._sentinel_emitted = True
                self._loop.call_soon_threadsafe(self._queue.put_nowait, None)
            self._done_event.set()

        elif event_type == "session.finished":
            logger.info("DashScope TTS: session finished")
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


class _SafeQwenTtsRealtime(QwenTtsRealtime):
    """DashScope SDK wrapper that does not re-raise websocket-client close noise."""

    def on_error(self, ws, error):  # pylint: disable=unused-argument
        error_message = str(error)
        if "Invalid close frame" in error_message:
            logger.debug("DashScope TTS websocket closed with invalid close frame")
            if self.callback:
                self.callback.on_close(None, error_message)
            return

        logger.error("DashScope TTS websocket error: %s", error_message)
        if self.callback:
            self.callback.on_event(
                {
                    "type": "error",
                    "error": {"message": error_message},
                }
            )


class DashScopeTTS(TTSBase):
    """DashScope Qwen CustomVoice realtime TTS."""

    def __init__(self, config: Settings):
        self._config = config

        # Set API key
        if config.dashscope_api_key:
            dashscope.api_key = config.dashscope_api_key

    async def _run_blocking(self, function, *args):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, function, *args)

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

        parts: list[str] = []
        async for text_chunk in text_iterator:
            if text_chunk.strip():
                parts.append(text_chunk)

        full_text = "".join(parts).strip()
        if not full_text:
            return

        loop = asyncio.get_running_loop()
        audio_queue: asyncio.Queue[Optional[bytes]] = asyncio.Queue()
        callback = _TTSCallback(audio_queue, loop)

        tts_client = _SafeQwenTtsRealtime(
            model=self._config.tts_model,
            callback=callback,
            url=self._config.dashscope_ws_url,
        )

        await self._run_blocking(tts_client.connect)

        session_payload = {
            "voice": cfg.voice,
            "response_format": AudioFormat.PCM_24000HZ_MONO_16BIT,
            "mode": "commit",
            "language_type": cfg.language,
        }
        if "instruct" in self._config.tts_model.lower() and self._config.tts_instructions:
            session_payload["instructions"] = self._config.tts_instructions
            session_payload["enable_instructions_optimization"] = self._config.tts_optimize_instructions

        await self._run_blocking(
            lambda: tts_client.update_session(**session_payload),
        )
        logger.info(
            "DashScope Qwen instruct TTS: session configured (model=%s, mode=commit, voice=%s, language=%s, instructions=%s, text_len=%s)",
            self._config.tts_model,
            cfg.voice,
            cfg.language,
            bool(session_payload.get("instructions")),
            len(full_text),
        )

        try:
            await self._run_blocking(tts_client.append_text, full_text)
            logger.info("DashScope TTS: committing text buffer (text_len=%s)", len(full_text))
            await self._run_blocking(tts_client.commit)
        except Exception as e:
            logger.error(f"Error sending text to TTS: {e}")
            await self._run_blocking(tts_client.close)
            return

        # Yield audio chunks as they arrive
        received_audio = False
        try:
            while True:
                try:
                    chunk = await asyncio.wait_for(audio_queue.get(), timeout=30.0)
                    if chunk is None:  # Sentinel: end of audio
                        break
                    received_audio = True
                    yield chunk
                except asyncio.TimeoutError:
                    logger.warning("TTS audio queue timeout")
                    break
        finally:
            await self._run_blocking(callback.wait_for_done, 5.0)
            try:
                await self._run_blocking(tts_client.close)
            except Exception as e:
                logger.debug(f"DashScope TTS close ignored: {e}")
            if not received_audio:
                logger.warning(
                    "DashScope TTS finished without audio; last_message=%s response_id=%s",
                    tts_client.get_last_message(),
                    tts_client.get_last_response_id(),
                )

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

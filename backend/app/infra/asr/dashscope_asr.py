"""
DashScope Realtime ASR provider.

Uses Alibaba Cloud's DashScope OmniRealtimeConversation for real-time
speech-to-text via WebSocket (model: qwen3-asr-flash-realtime).
"""

import asyncio
import base64
import logging
import threading
from typing import Optional

import dashscope
from dashscope.audio.qwen_omni import (
    MultiModality,
    OmniRealtimeCallback,
    OmniRealtimeConversation,
)
from dashscope.audio.qwen_omni.omni_realtime import TranscriptionParams

from app.core.config import Settings
from app.infra.contracts import ASRBase, TranscriptEvent, TranscriptType

logger = logging.getLogger(__name__)


class _ASRCallback(OmniRealtimeCallback):
    """Callback handler for DashScope realtime ASR events."""

    def __init__(self, transcript_queue: asyncio.Queue, loop: asyncio.AbstractEventLoop):
        self._queue = transcript_queue
        self._loop = loop
        self._closed_event = threading.Event()

    def on_open(self):
        logger.info("DashScope ASR: connection opened")

    def on_close(self, code, msg):
        logger.info(f"DashScope ASR: connection closed (code={code}, msg={msg})")
        self._closed_event.set()

    def on_event(self, response):
        event_type = response.get("type", "")

        if event_type == "conversation.item.input_audio_transcription.completed":
            transcript = response.get("transcript", "")
            if transcript.strip():
                event = TranscriptEvent(
                    text=transcript.strip(),
                    type=TranscriptType.FINAL,
                )
                self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

        elif event_type == "conversation.item.input_audio_transcription.text":
            stash = response.get("stash", "")
            if stash.strip():
                event = TranscriptEvent(
                    text=stash.strip(),
                    type=TranscriptType.PARTIAL,
                )
                self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

        elif event_type == "input_audio_buffer.speech_started":
            logger.debug("DashScope ASR: speech started")

        elif event_type == "input_audio_buffer.speech_stopped":
            logger.debug("DashScope ASR: speech stopped")
            event = TranscriptEvent(
                text="",
                type=TranscriptType.SPEECH_END,
            )
            self._loop.call_soon_threadsafe(self._queue.put_nowait, event)

        elif event_type == "error":
            error_msg = response.get("error", {}).get("message", "Unknown error")
            logger.error(f"DashScope ASR error: {error_msg}")

    def wait_for_close(self, timeout: float = 5.0):
        self._closed_event.wait(timeout=timeout)


class DashScopeASR(ASRBase):
    """DashScope Realtime ASR using qwen3-asr-flash-realtime."""

    def __init__(self, config: Settings):
        self._config = config
        self._conversation: Optional[OmniRealtimeConversation] = None
        self._transcript_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()
        self._connected = False
        self._callback: Optional[_ASRCallback] = None

        # Set API key
        if config.dashscope_api_key:
            dashscope.api_key = config.dashscope_api_key

    async def start_session(self, language: str = "en", sample_rate: int = 16000) -> None:
        """Start a new ASR streaming session."""
        if self._connected:
            await self.stop_session()

        loop = asyncio.get_event_loop()
        self._transcript_queue = asyncio.Queue()

        callback = _ASRCallback(self._transcript_queue, loop)
        self._callback = callback

        self._conversation = OmniRealtimeConversation(
            model=self._config.asr_model,
            url=self._config.dashscope_ws_url,
            callback=callback,
        )

        # Connect in a thread to avoid blocking the event loop
        await asyncio.get_event_loop().run_in_executor(
            None, self._conversation.connect
        )

        # Configure session
        transcription_params = TranscriptionParams(
            language=language,
            sample_rate=sample_rate,
            input_audio_format="pcm",
        )
        self._conversation.update_session(
            output_modalities=[MultiModality.TEXT],
            enable_input_audio_transcription=True,
            transcription_params=transcription_params,
        )

        self._connected = True
        logger.info(f"DashScope ASR session started (language={language}, rate={sample_rate})")

    async def feed_audio(self, audio_chunk: bytes) -> None:
        """Feed PCM audio chunk to the ASR engine."""
        if not self._connected or not self._conversation:
            logger.warning("ASR: tried to feed audio without active session")
            return

        audio_b64 = base64.b64encode(audio_chunk).decode("ascii")
        # Run in executor to avoid blocking
        await asyncio.get_event_loop().run_in_executor(
            None, self._conversation.append_audio, audio_b64
        )

    async def get_transcript(self) -> Optional[TranscriptEvent]:
        """Get next transcript event (non-blocking)."""
        try:
            return self._transcript_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def stop_session(self) -> Optional[TranscriptEvent]:
        """Stop session and return any remaining transcript."""
        if not self._connected or not self._conversation:
            return None

        try:
            await asyncio.get_event_loop().run_in_executor(
                None, self._conversation.end_session
            )
        except Exception as e:
            logger.error(f"Error ending ASR session: {e}")
        finally:
            if self._callback:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._callback.wait_for_close, 5.0
                )
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._conversation.close
                )
            except Exception as e:
                logger.debug(f"DashScope ASR close ignored: {e}")

        self._connected = False
        self._conversation = None
        self._callback = None

        # Return last transcript if available
        last = None
        while not self._transcript_queue.empty():
            last = self._transcript_queue.get_nowait()
        return last

    async def close(self) -> None:
        """Close the ASR connection."""
        if self._conversation:
            try:
                await asyncio.get_event_loop().run_in_executor(
                    None, self._conversation.close
                )
            except Exception as e:
                logger.debug(f"DashScope ASR close ignored: {e}")
            self._conversation = None
            self._connected = False
            self._callback = None

"""
Conversation manager: orchestrates the ASR → LLM → TTS pipeline.

Each WebSocket session creates a ConversationSession that manages:
- Service lifecycle (create/destroy providers)
- Conversation history
- Audio streaming pipeline
"""

import asyncio
import logging
from typing import AsyncGenerator, Callable, Optional

from app.config import Settings
from app.services.base import ASRBase, LLMBase, TTSBase, Message, TranscriptType
from app.services.factory import create_asr, create_llm, create_tts

logger = logging.getLogger(__name__)


class ConversationSession:
    """
    Manages a single conversation session.

    Orchestrates the flow: audio → ASR → LLM → TTS → audio
    """

    def __init__(self, config: Settings):
        self._config = config
        self._asr: Optional[ASRBase] = None
        self._llm: Optional[LLMBase] = None
        self._tts: Optional[TTSBase] = None
        self._messages: list[Message] = []
        self._is_recording = False
        self._asr_poll_task: Optional[asyncio.Task] = None

        # Callbacks for sending events back to WebSocket
        self._on_transcript: Optional[Callable] = None
        self._on_llm_chunk: Optional[Callable] = None
        self._on_audio_chunk: Optional[Callable] = None
        self._on_error: Optional[Callable] = None

    async def initialize(
        self,
        on_transcript: Callable,
        on_llm_chunk: Callable,
        on_audio_chunk: Callable,
        on_error: Callable,
    ):
        """Initialize services and set up callbacks."""
        self._on_transcript = on_transcript
        self._on_llm_chunk = on_llm_chunk
        self._on_audio_chunk = on_audio_chunk
        self._on_error = on_error

        try:
            self._asr = create_asr(self._config)
            self._llm = create_llm(self._config)
            self._tts = create_tts(self._config)
            logger.info("ConversationSession: all services initialized")
        except Exception as e:
            logger.error(f"Failed to initialize services: {e}")
            if self._on_error:
                await self._on_error(str(e))
            raise

    async def start_recording(self, language: str = "en") -> None:
        """Start recording and ASR processing."""
        if self._is_recording:
            return

        try:
            await self._asr.start_session(language=language)
            self._is_recording = True

            # Start polling for transcripts
            self._asr_poll_task = asyncio.create_task(self._poll_transcripts())

            logger.info("Recording started")
        except Exception as e:
            logger.error(f"Error starting recording: {e}")
            if self._on_error:
                await self._on_error(f"Failed to start recording: {e}")

    async def feed_audio(self, audio_chunk: bytes) -> None:
        """Feed audio data to ASR."""
        if not self._is_recording or not self._asr:
            return

        try:
            await self._asr.feed_audio(audio_chunk)
        except Exception as e:
            logger.error(f"Error feeding audio: {e}")

    async def stop_recording(self) -> None:
        """Stop recording, finalize ASR, and trigger LLM + TTS pipeline."""
        if not self._is_recording:
            return

        self._is_recording = False

        # Cancel poll task
        if self._asr_poll_task:
            self._asr_poll_task.cancel()
            try:
                await self._asr_poll_task
            except asyncio.CancelledError:
                pass

        # Get final transcript
        final_event = None
        try:
            final_event = await self._asr.stop_session()
        except Exception as e:
            logger.error(f"Error stopping ASR session: {e}")

        if final_event and final_event.text.strip():
            # Notify frontend of final transcript
            if self._on_transcript:
                await self._on_transcript(final_event.text, "final")

            # Run LLM → TTS pipeline
            await self._run_response_pipeline(final_event.text)
        else:
            logger.info("No transcript from recording")

    async def _poll_transcripts(self):
        """Poll ASR for transcript events while recording."""
        try:
            while self._is_recording:
                if self._asr:
                    event = await self._asr.get_transcript()
                    if event and self._on_transcript:
                        await self._on_transcript(
                            event.text,
                            event.type.value,
                        )
                await asyncio.sleep(0.1)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error polling transcripts: {e}")

    async def _run_response_pipeline(self, user_text: str) -> None:
        """Run the LLM → TTS pipeline for a user message."""

        # Add user message to history
        self._messages.append(Message(role="user", content=user_text))

        # Stream LLM response
        full_response = ""

        async def _llm_text_stream():
            """Generator that streams LLM text and collects full response."""
            nonlocal full_response
            try:
                async for chunk in self._llm.chat_stream(self._messages):
                    full_response += chunk

                    # Notify frontend of LLM chunk
                    if self._on_llm_chunk:
                        await self._on_llm_chunk(chunk, False)

                    yield chunk
            except Exception as e:
                logger.error(f"LLM streaming error: {e}")
                error_msg = f"Sorry, I had trouble generating a response."
                full_response = error_msg
                yield error_msg

        # Stream LLM text → TTS → audio chunks
        try:
            async for audio_chunk in self._tts.synthesize_stream(_llm_text_stream()):
                if self._on_audio_chunk:
                    await self._on_audio_chunk(audio_chunk)
        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
            if self._on_error:
                await self._on_error(f"TTS error: {e}")

        # Notify LLM done
        if self._on_llm_chunk:
            await self._on_llm_chunk(full_response, True)

        # Signal audio done
        if self._on_audio_chunk:
            await self._on_audio_chunk(None)  # None = sentinel for "audio done"

        # Add assistant response to history
        if full_response:
            self._messages.append(Message(role="assistant", content=full_response))

        logger.info(f"Response pipeline complete (response_len={len(full_response)})")

    async def close(self) -> None:
        """Clean up all resources."""
        self._is_recording = False

        if self._asr_poll_task:
            self._asr_poll_task.cancel()

        for service in [self._asr, self._llm, self._tts]:
            if service:
                try:
                    await service.close()
                except Exception as e:
                    logger.error(f"Error closing service: {e}")

        self._messages.clear()
        logger.info("ConversationSession closed")

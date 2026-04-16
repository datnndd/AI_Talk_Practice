"""
Conversation manager: orchestrates the ASR → LLM → TTS pipeline.

Each WebSocket session creates a ConversationSession that manages:
- Service lifecycle (create/destroy providers)
- Conversation history
- Audio streaming pipeline
"""

import asyncio
import logging
import time
from typing import Awaitable, Callable, Optional

from app.core.config import Settings
from app.infra.contracts import ASRBase, LLMBase, Message, TTSBase, TTSConfig, TranscriptEvent, TranscriptType
from app.infra.factory import create_asr, create_llm, create_tts
from app.modules.sessions.services.lesson_runtime import chunk_text_for_stream

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
        self._on_user_message: Optional[Callable[[str], Awaitable[None]]] = None
        self._on_assistant_message: Optional[Callable[[str], Awaitable[None]]] = None
        self._on_generate_reply: Optional[Callable[[str], Awaitable[str]]] = None
        self._system_prompt: Optional[str] = None
        self._language = config.asr_language
        self._voice = config.tts_voice
        self._response_task: Optional[asyncio.Task] = None
        self._current_response_text = ""
        self._latest_partial_transcript = ""
        self._final_transcript_text = ""
        self._asr_finalize_task: Optional[asyncio.Task] = None
        self._turn_finalized = False
        self._turn_timing: dict[str, float] = {}

    async def initialize(
        self,
        on_transcript: Callable,
        on_llm_chunk: Callable,
        on_audio_chunk: Callable,
        on_error: Callable,
        system_prompt: Optional[str] = None,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        on_user_message: Optional[Callable[[str], Awaitable[None]]] = None,
        on_assistant_message: Optional[Callable[[str], Awaitable[None]]] = None,
        on_generate_reply: Optional[Callable[[str], Awaitable[str]]] = None,
    ):
        """Initialize services and set up callbacks."""
        self._on_transcript = on_transcript
        self._on_llm_chunk = on_llm_chunk
        self._on_audio_chunk = on_audio_chunk
        self._on_error = on_error
        self._system_prompt = system_prompt
        self._on_user_message = on_user_message
        self._on_assistant_message = on_assistant_message
        self._on_generate_reply = on_generate_reply
        if language:
            self._language = language
        if voice:
            self._voice = voice

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

    def update_config(
        self,
        *,
        language: Optional[str] = None,
        voice: Optional[str] = None,
    ) -> tuple[str, str]:
        """Update the active conversation config for subsequent turns."""
        if language:
            self._language = language
        if voice:
            self._voice = voice
        return self._language, self._voice

    async def start_recording(self, language: str = "en") -> None:
        """Start recording and ASR processing."""
        if self._is_recording:
            return

        try:
            self._language = language or self._language
            self._latest_partial_transcript = ""
            self._final_transcript_text = ""
            self._turn_finalized = False
            self._turn_timing = {}
            await self._cancel_asr_finalize_task()
            await self._asr.start_session(language=self._language)
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

        await self._finalize_recording_turn()

    async def interrupt_response(self) -> str:
        """Interrupt the active assistant response and return any partial text."""
        task = self._response_task
        if task is None:
            return self._current_response_text.strip()

        if task.done():
            try:
                _, partial_text = task.result()
                return partial_text.strip()
            except Exception as e:
                logger.error(f"Response task finished with error: {e}")
                return self._current_response_text.strip()
            finally:
                if task is self._response_task:
                    self._response_task = None

        task.cancel()
        try:
            _, partial_text = await task
            return partial_text.strip()
        except asyncio.CancelledError:
            return self._current_response_text.strip()
        except Exception as e:
            logger.error(f"Error interrupting assistant response: {e}")
            return self._current_response_text.strip()
        finally:
            if task is self._response_task:
                self._response_task = None

    async def _start_response_pipeline(self, user_text: str) -> None:
        """Start the assistant response pipeline as a background task."""
        if self._response_task and not self._response_task.done():
            await self.interrupt_response()

        self._current_response_text = ""
        task = asyncio.create_task(self._run_response_pipeline(user_text))
        self._response_task = task
        task.add_done_callback(self._handle_response_task_done)

    def _handle_response_task_done(self, task: asyncio.Task) -> None:
        if task is self._response_task:
            self._response_task = None

        try:
            task.result()
        except asyncio.CancelledError:
            logger.info("Assistant response task cancelled")
        except Exception as e:
            logger.error(f"Assistant response task failed: {e}")

    async def _poll_transcripts(self):
        """Poll ASR for transcript events while recording."""
        try:
            while self._is_recording:
                if self._asr:
                    event = await self._asr.get_transcript()
                    if event:
                        if event.type == TranscriptType.PARTIAL and event.text.strip():
                            self._latest_partial_transcript = event.text.strip()

                        if event.type == TranscriptType.SPEECH_END:
                            self._schedule_asr_finalization("speech_end")

                        if event.type == TranscriptType.FINAL and event.text.strip():
                            self._remember_final_transcript(event.text)
                            self._schedule_asr_finalization("final_transcript")

                        if (
                            self._config.asr_emit_partial_transcripts
                            and event.type == TranscriptType.PARTIAL
                            and self._on_transcript
                        ):
                            await self._on_transcript(
                                event.text,
                                event.type.value,
                            )
                await asyncio.sleep(0.03)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"Error polling transcripts: {e}")
        finally:
            if asyncio.current_task() is self._asr_poll_task:
                self._asr_poll_task = None

    def _remember_final_transcript(self, text: str) -> None:
        """Keep the most complete final transcript text seen for this turn."""
        clean = text.strip()
        if not clean:
            return

        current = self._final_transcript_text.strip()
        if not current:
            self._final_transcript_text = clean
        elif clean == current or clean in current:
            return
        elif current in clean:
            self._final_transcript_text = clean
        else:
            self._final_transcript_text = f"{current} {clean}".strip()

    def _select_turn_transcript(self, final_event: Optional[TranscriptEvent]) -> str:
        """Choose the best available transcript after ASR has been stopped."""
        if final_event and final_event.text.strip():
            if final_event.type == TranscriptType.FINAL:
                self._remember_final_transcript(final_event.text)
            elif not self._final_transcript_text:
                self._latest_partial_transcript = final_event.text.strip()

        final_text = self._final_transcript_text.strip()
        partial_text = self._latest_partial_transcript.strip()
        if final_text and partial_text and final_text in partial_text:
            return partial_text
        return final_text or partial_text

    def _schedule_asr_finalization(self, reason: str) -> None:
        """Finalize shortly after ASR says the utterance is done.

        The delay is intentional: browser audio callbacks and provider events can
        arrive slightly out of order, and closing immediately can drop the last
        syllables of the user's turn.
        """
        if self._turn_finalized:
            return

        if self._asr_finalize_task and not self._asr_finalize_task.done():
            self._asr_finalize_task.cancel()

        self._asr_finalize_task = asyncio.create_task(self._finalize_after_grace(reason))

    async def _finalize_after_grace(self, reason: str) -> None:
        delay = max(0, self._config.asr_finalization_grace_ms) / 1000
        try:
            await asyncio.sleep(delay)
            logger.info("Finalizing ASR turn after %sms grace period (%s)", int(delay * 1000), reason)
            await self._finalize_recording_turn()
        except asyncio.CancelledError:
            pass

    async def _cancel_asr_poll_task(self) -> None:
        if not self._asr_poll_task:
            return

        task = self._asr_poll_task
        if task is asyncio.current_task():
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            if task is self._asr_poll_task:
                self._asr_poll_task = None

    async def _cancel_asr_finalize_task(self) -> None:
        if not self._asr_finalize_task:
            return

        task = self._asr_finalize_task
        if task is asyncio.current_task():
            return

        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
        finally:
            if task is self._asr_finalize_task:
                self._asr_finalize_task = None

    async def _finalize_recording_turn(self) -> None:
        """Stop ASR once, choose the best transcript, and complete the turn."""
        if self._turn_finalized:
            return

        self._turn_finalized = True
        self._is_recording = False
        self._mark_turn_phase("user_stop")

        await self._cancel_asr_finalize_task()
        await self._cancel_asr_poll_task()

        final_event = await self._stop_asr_session()
        await self._handle_completed_turn(self._select_turn_transcript(final_event))

    async def _stop_asr_session(self) -> Optional[TranscriptEvent]:
        """Stop the active ASR session and return the last queued transcript event."""
        if not self._asr:
            return None

        try:
            return await self._asr.stop_session()
        except Exception as e:
            logger.error(f"Error stopping ASR session: {e}")
            return None

    async def _handle_completed_turn(self, final_text: Optional[str]) -> None:
        """Forward a completed user turn to the frontend and launch the assistant reply."""
        text = (final_text or "").strip()
        if not text:
            logger.info("No transcript from recording")
            return

        self._latest_partial_transcript = text
        self._mark_turn_phase("asr_final_ready")

        if self._on_transcript:
            await self._on_transcript(text, TranscriptType.FINAL.value)

        self._messages.append(Message(role="user", content=text))
        if self._on_user_message:
            await self._on_user_message(text)

        # Run LLM → TTS pipeline in the background so the websocket
        # can still accept interrupt messages while the assistant speaks.
        await self._start_response_pipeline(text)

    async def _run_response_pipeline(self, user_text: str) -> tuple[bool, str]:
        """Run the LLM → TTS pipeline for a user message."""
        last_message = self._messages[-1] if self._messages else None
        user_turn_already_recorded = (
            last_message is not None
            and last_message.role == "user"
            and last_message.content == user_text
        )

        if not user_turn_already_recorded:
            self._messages.append(Message(role="user", content=user_text))
            if self._on_user_message:
                await self._on_user_message(user_text)

        if self._on_generate_reply:
            return await self._run_custom_reply_pipeline(user_text)

        # Stream LLM response
        full_response = ""
        interrupted = False
        text_queue: asyncio.Queue[Optional[str]] = asyncio.Queue()
        llm_task: Optional[asyncio.Task] = None

        async def _queue_text_stream():
            """Yield text chunks from the LLM queue to the TTS pipeline."""
            while True:
                chunk = await text_queue.get()
                if chunk is None:
                    break
                yield chunk

        async def _llm_producer():
            """Stream LLM text to the frontend immediately and enqueue it for TTS."""
            nonlocal full_response
            try:
                llm_messages = self._select_llm_messages()
                async for chunk in self._llm.chat_stream(llm_messages, system_prompt=self._system_prompt):
                    full_response += chunk
                    self._current_response_text = full_response
                    if "llm_first_token" not in self._turn_timing:
                        self._mark_turn_phase("llm_first_token")

                    if self._on_llm_chunk:
                        await self._on_llm_chunk(chunk, False)

                    await text_queue.put(chunk)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"LLM streaming error: {e}")
                error_msg = f"Sorry, I had trouble generating a response."
                full_response = error_msg
                self._current_response_text = full_response
                if self._on_llm_chunk:
                    await self._on_llm_chunk(error_msg, False)
                await text_queue.put(error_msg)
            finally:
                await text_queue.put(None)

        llm_task = asyncio.create_task(_llm_producer())

        try:
            tts_config = TTSConfig(
                voice=self._voice,
                language=self._language,
            )
            async for audio_chunk in self._tts.synthesize_stream(
                _queue_text_stream(),
                config=tts_config,
            ):
                if "tts_first_audio" not in self._turn_timing:
                    self._mark_turn_phase("tts_first_audio")
                if self._on_audio_chunk:
                    await self._on_audio_chunk(audio_chunk)
            await llm_task
        except asyncio.CancelledError:
            interrupted = True
            if llm_task and not llm_task.done():
                llm_task.cancel()
                try:
                    await llm_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
            if self._on_error:
                await self._on_error(f"TTS error: {e}")
            if llm_task:
                await llm_task

        self._current_response_text = full_response

        # Notify LLM done only when the response completed normally.
        if not interrupted and self._on_llm_chunk:
            await self._on_llm_chunk(full_response, True)

        # Signal audio done
        if self._on_audio_chunk:
            await self._on_audio_chunk(None)  # None = sentinel for "audio done"

        # Add assistant response to history
        if full_response:
            self._messages.append(Message(role="assistant", content=full_response))
            if self._on_assistant_message:
                await self._on_assistant_message(full_response)

        logger.info(
            "Response pipeline complete (response_len=%s interrupted=%s)",
            len(full_response),
            interrupted,
        )
        self._log_turn_timing(response_len=len(full_response), interrupted=interrupted)
        return interrupted, full_response

    async def _run_custom_reply_pipeline(self, user_text: str) -> tuple[bool, str]:
        """Run a structured reply pipeline where the text is generated outside the LLM stream."""
        interrupted = False
        full_response = ""

        try:
            full_response = (await self._on_generate_reply(user_text)).strip()
            self._current_response_text = ""
        except Exception as e:
            logger.error(f"Structured reply generation error: {e}")
            full_response = "Sorry, I had trouble preparing the next step."

        async def _text_stream():
            for chunk in chunk_text_for_stream(full_response or "Sorry, I had trouble preparing the next step."):
                self._current_response_text = f"{self._current_response_text}{chunk}"
                if "llm_first_token" not in self._turn_timing:
                    self._mark_turn_phase("llm_first_token")
                if self._on_llm_chunk:
                    await self._on_llm_chunk(chunk, False)
                yield chunk

        try:
            tts_config = TTSConfig(
                voice=self._voice,
                language=self._language,
            )
            async for audio_chunk in self._tts.synthesize_stream(_text_stream(), config=tts_config):
                if "tts_first_audio" not in self._turn_timing:
                    self._mark_turn_phase("tts_first_audio")
                if self._on_audio_chunk:
                    await self._on_audio_chunk(audio_chunk)
        except asyncio.CancelledError:
            interrupted = True
        except Exception as e:
            logger.error(f"TTS streaming error: {e}")
            if self._on_error:
                await self._on_error(f"TTS error: {e}")

        self._current_response_text = full_response

        if not interrupted and self._on_llm_chunk:
            await self._on_llm_chunk(full_response, True)

        if self._on_audio_chunk:
            await self._on_audio_chunk(None)

        if full_response:
            self._messages.append(Message(role="assistant", content=full_response))
            if self._on_assistant_message:
                await self._on_assistant_message(full_response)

        logger.info(
            "Structured response pipeline complete (response_len=%s interrupted=%s)",
            len(full_response),
            interrupted,
        )
        self._log_turn_timing(response_len=len(full_response), interrupted=interrupted)
        return interrupted, full_response

    def _select_llm_messages(self) -> list[Message]:
        """Return only the most recent conversation turns for the LLM context window."""
        message_limit = max(1, int(self._config.llm_history_message_limit))
        if len(self._messages) <= message_limit:
            return list(self._messages)
        return list(self._messages[-message_limit:])

    def _mark_turn_phase(self, phase: str) -> None:
        """Record a monotonic timestamp for a turn phase once."""
        if phase not in self._turn_timing:
            self._turn_timing[phase] = time.perf_counter()

    def _log_turn_timing(self, *, response_len: int, interrupted: bool) -> None:
        """Emit phase timing deltas for a completed assistant response."""
        user_stop = self._turn_timing.get("user_stop")
        asr_final = self._turn_timing.get("asr_final_ready")
        llm_first = self._turn_timing.get("llm_first_token")
        tts_first = self._turn_timing.get("tts_first_audio")

        def _ms(current: float | None, previous: float | None) -> int | None:
            if current is None or previous is None:
                return None
            return max(0, int((current - previous) * 1000))

        logger.info(
            "Turn timing: asr_final_ms=%s llm_first_token_ms=%s tts_first_audio_ms=%s interrupted=%s response_len=%s",
            _ms(asr_final, user_stop),
            _ms(llm_first, user_stop),
            _ms(tts_first, user_stop),
            interrupted,
            response_len,
        )

    async def speak_opening(self, text: str) -> None:
        """Speak the assistant's opening message through the TTS pipeline.

        This allows the assistant to proactively start the conversation
        without waiting for a user turn.
        """
        text = text.strip()
        if not text:
            return

        self._messages.append(Message(role="assistant", content=text))
        if self._on_assistant_message:
            await self._on_assistant_message(text)

        async def _text_stream():
            for chunk in chunk_text_for_stream(text):
                self._current_response_text = f"{self._current_response_text}{chunk}"
                self._mark_turn_phase("llm_first_token")
                if self._on_llm_chunk:
                    await self._on_llm_chunk(chunk, False)
                yield chunk

        try:
            tts_config = TTSConfig(voice=self._voice, language=self._language)
            async for audio_chunk in self._tts.synthesize_stream(_text_stream(), config=tts_config):
                self._mark_turn_phase("tts_first_audio")
                if self._on_audio_chunk:
                    await self._on_audio_chunk(audio_chunk)
        except Exception as e:
            logger.error(f"TTS error during opening speech: {e}")
            if self._on_error:
                await self._on_error(f"TTS error: {e}")

        self._current_response_text = text
        if self._on_llm_chunk:
            await self._on_llm_chunk(text, True)
        if self._on_audio_chunk:
            await self._on_audio_chunk(None)

        logger.info("Opening message spoken (len=%s)", len(text))

    async def close(self) -> None:
        """Clean up all resources."""
        self._is_recording = False

        await self._cancel_asr_finalize_task()

        if self._asr_poll_task:
            self._asr_poll_task.cancel()
            try:
                await self._asr_poll_task
            except asyncio.CancelledError:
                pass
            except Exception as e:
                logger.error(f"Error canceling ASR poll task: {e}")

        if self._response_task and not self._response_task.done():
            try:
                await asyncio.wait_for(asyncio.shield(self._response_task), timeout=2.0)
            except asyncio.TimeoutError:
                await self.interrupt_response()
            except Exception as e:
                logger.error(f"Error waiting for response task during close: {e}")

        # Close all active services in parallel
        services_to_close = [s for s in [self._asr, self._llm, self._tts] if s]
        if services_to_close:
            try:
                results = await asyncio.gather(
                    *[s.close() for s in services_to_close],
                    return_exceptions=True
                )
                for res in results:
                    if isinstance(res, Exception):
                        logger.error(f"Error during parallel service cleanup: {res}")
            except Exception as e:
                logger.error(f"Unexpected error during service cleanup: {e}")

        self._messages.clear()
        logger.info("ConversationSession closed")

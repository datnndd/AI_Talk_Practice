"""
Deepgram realtime ASR provider.

Streams PCM audio to Deepgram's Nova WebSocket API and converts websocket
messages into the app's TranscriptEvent contract.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from app.core.config import Settings
from app.infra.contracts import ASRBase, TranscriptEvent, TranscriptType

logger = logging.getLogger(__name__)
payload_logger = logging.getLogger("deepgram_asr")


class DeepgramASR(ASRBase):
    """Deepgram realtime ASR using the Nova streaming model."""

    def __init__(self, config: Settings):
        self._config = config
        self._language = config.asr_language
        self._sample_rate = 16000
        self._websocket: ClientConnection | None = None
        self._transcript_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()
        self._receiver_task: asyncio.Task | None = None
        self._keepalive_task: asyncio.Task | None = None
        self._connected = False
        self._final_segments: list[str] = []
        self._latest_partial = ""

    async def start_session(self, language: str = "en", sample_rate: int = 16000) -> None:
        if self._connected:
            await self.stop_session()

        if not self._config.deepgram_api_key:
            raise ValueError("Deepgram ASR requires DEEPGRAM_API_KEY")

        self._language = language
        self._sample_rate = sample_rate
        self._transcript_queue = asyncio.Queue()
        self._final_segments = []
        self._latest_partial = ""
        self._ensure_payload_logger()

        query_params: dict[str, str | int | float] = {
            "model": self._config.deepgram_asr_model,
            "language": language,
            "encoding": "linear16",
            "sample_rate": sample_rate,
            "channels": 1,
            "smart_format": self._bool_query(self._config.deepgram_smart_format),
            "interim_results": self._bool_query(self._config.deepgram_interim_results),
            "endpointing": self._config.deepgram_endpointing_ms,
        }
        if self._config.deepgram_interim_results:
            query_params["utterance_end_ms"] = self._config.deepgram_utterance_end_ms
        query = urlencode(query_params)
        url = f"{self._config.deepgram_ws_url}?{query}"

        self._websocket = await connect(
            url,
            additional_headers={
                "Authorization": f"Token {self._config.deepgram_api_key}",
            },
            max_size=None,
            ping_interval=20,
            ping_timeout=20,
            open_timeout=10,
        )
        self._connected = True
        self._receiver_task = asyncio.create_task(self._receive_messages())
        self._keepalive_task = asyncio.create_task(self._send_keepalive())
        logger.info(
            "Deepgram Nova ASR session started (model=%s, language=%s, rate=%s)",
            self._config.deepgram_asr_model,
            language,
            sample_rate,
        )
        if self._config.deepgram_log_payloads:
            payload_logger.info(
                "Deepgram ASR session started model=%s language=%s sample_rate=%s",
                self._config.deepgram_asr_model,
                language,
                sample_rate,
            )

    async def feed_audio(self, audio_chunk: bytes) -> None:
        if not self._connected or self._websocket is None:
            logger.warning("Deepgram ASR: tried to feed audio without an active session")
            return
        await self._websocket.send(audio_chunk)

    async def get_transcript(self) -> TranscriptEvent | None:
        try:
            return self._transcript_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

    async def stop_session(self) -> TranscriptEvent | None:
        if not self._connected or self._websocket is None:
            return None

        websocket = self._websocket
        self._connected = False

        try:
            await websocket.send(json.dumps({"type": "Finalize"}))
        except Exception as exc:
            logger.debug("Deepgram ASR finalize command failed: %s", exc)

        try:
            await websocket.send(json.dumps({"type": "CloseStream"}))
        except Exception as exc:
            logger.debug("Deepgram ASR close command failed: %s", exc)

        if self._receiver_task is not None:
            try:
                await asyncio.wait_for(self._receiver_task, timeout=1.0)
            except asyncio.TimeoutError:
                self._receiver_task.cancel()
                try:
                    await self._receiver_task
                except asyncio.CancelledError:
                    pass
            finally:
                self._receiver_task = None

        if self._keepalive_task is not None:
            self._keepalive_task.cancel()
            try:
                await self._keepalive_task
            except asyncio.CancelledError:
                pass
            finally:
                self._keepalive_task = None

        await self._close_websocket(websocket)
        self._websocket = None

        return self._drain_transcript_queue()

    async def close(self) -> None:
        self._connected = False
        await self._shutdown_background_tasks()
        if self._websocket is not None:
            await self._close_websocket(self._websocket)
            self._websocket = None

    async def _receive_messages(self) -> None:
        websocket = self._websocket
        if websocket is None:
            return

        try:
            async for raw_message in websocket:
                if isinstance(raw_message, bytes):
                    if self._config.deepgram_log_payloads:
                        payload_logger.info("Deepgram raw binary response bytes=%s", len(raw_message))
                    continue
                if self._config.deepgram_log_payloads:
                    payload_logger.info("Deepgram raw response: %s", raw_message)
                payload = self._load_json(raw_message)
                if payload is None:
                    continue
                self._handle_payload(payload)
        except asyncio.CancelledError:
            raise
        except ConnectionClosed as exc:
            logger.info("Deepgram ASR websocket closed (code=%s, reason=%s)", exc.code, exc.reason)
        except Exception:
            logger.exception("Deepgram ASR receiver failed")

    async def _send_keepalive(self) -> None:
        try:
            while self._connected and self._websocket is not None:
                await asyncio.sleep(self._config.deepgram_keepalive_seconds)
                if not self._connected or self._websocket is None:
                    break
                await self._websocket.send(json.dumps({"type": "KeepAlive"}))
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.debug("Deepgram ASR keepalive failed: %s", exc)

    def _handle_payload(self, payload: Mapping[str, Any]) -> None:
        message_type = str(payload.get("type") or "")

        if message_type in {"Results", "Transcript"}:
            channel = payload.get("channel") or {}
            alternatives = channel.get("alternatives") or []
            transcript = ""
            if alternatives and isinstance(alternatives[0], Mapping):
                transcript = str(alternatives[0].get("transcript") or "").strip()
            if not transcript:
                transcript = str(payload.get("transcript") or payload.get("text") or "").strip()
            language = self._extract_language(channel)
            is_final = bool(payload.get("is_final") or payload.get("final"))
            speech_final = bool(payload.get("speech_final") or payload.get("end_of_turn"))
            confidence = self._extract_confidence(alternatives)
            from_finalize = bool(payload.get("from_finalize"))
            logger.info(
                "Deepgram result flags is_final=%s speech_final=%s from_finalize=%s confidence=%s transcript_len=%s",
                is_final,
                speech_final,
                from_finalize,
                confidence,
                len(transcript),
            )

            if transcript:
                event_type = TranscriptType.FINAL if is_final else TranscriptType.PARTIAL
                if is_final:
                    self._remember_final_segment(transcript)
                else:
                    self._latest_partial = transcript
                self._transcript_queue.put_nowait(
                    TranscriptEvent(
                        text=transcript,
                        type=event_type,
                        language=language,
                    )
                )

            if speech_final:
                self._transcript_queue.put_nowait(
                    TranscriptEvent(
                        text="",
                        type=TranscriptType.SPEECH_END,
                        language=language,
                    )
                )
            return

        if message_type == "TurnInfo":
            event = str(payload.get("event") or "")
            transcript = str(payload.get("transcript") or payload.get("text") or "").strip()
            is_final = event.lower() in {"endofturn", "end_of_turn", "end-of-turn"}
            if transcript:
                if is_final:
                    self._remember_final_segment(transcript)
                else:
                    self._latest_partial = transcript
                self._transcript_queue.put_nowait(
                    TranscriptEvent(
                        text=transcript,
                        type=TranscriptType.FINAL if is_final else TranscriptType.PARTIAL,
                        language=self._language,
                    )
                )
            if is_final:
                self._transcript_queue.put_nowait(
                    TranscriptEvent(
                        text="",
                        type=TranscriptType.SPEECH_END,
                        language=self._language,
                    )
                )
            return

        if message_type == "UtteranceEnd":
            if not self._config.deepgram_interim_results:
                logger.debug("Deepgram ASR ignored UtteranceEnd because interim results are disabled")
                return
            if payload.get("last_word_end") == -1:
                return
            self._transcript_queue.put_nowait(
                TranscriptEvent(
                    text="",
                    type=TranscriptType.SPEECH_END,
                    language=self._language,
                )
            )
            return

        if message_type in {"EndOfTurn", "TurnEnd"}:
            self._transcript_queue.put_nowait(
                TranscriptEvent(
                    text="",
                    type=TranscriptType.SPEECH_END,
                    language=self._language,
                )
            )
            return

        if message_type == "SpeechStarted":
            logger.debug("Deepgram ASR: speech started")
            return

        if message_type == "Metadata":
            logger.debug("Deepgram ASR metadata received")
            return

        if message_type == "Error":
            logger.error("Deepgram ASR error payload: %s", payload)
            return

        logger.debug("Deepgram ASR unhandled payload type=%s", message_type)

    @staticmethod
    def _bool_query(value: bool) -> str:
        return "true" if value else "false"

    @staticmethod
    def _extract_confidence(alternatives: Any) -> float | None:
        if alternatives and isinstance(alternatives[0], Mapping):
            confidence = alternatives[0].get("confidence")
            if isinstance(confidence, int | float):
                return round(float(confidence), 6)
        return None

    def _ensure_payload_logger(self) -> None:
        if not self._config.deepgram_log_payloads:
            return

        log_path = os.path.abspath(self._config.deepgram_log_file)
        os.makedirs(os.path.dirname(log_path) or ".", exist_ok=True)
        if any(
            isinstance(handler, logging.FileHandler)
            and os.path.abspath(getattr(handler, "baseFilename", "")) == log_path
            for handler in payload_logger.handlers
        ):
            return

        handler = logging.FileHandler(log_path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s"))
        payload_logger.addHandler(handler)
        payload_logger.setLevel(logging.INFO)
        payload_logger.propagate = False

    def _drain_transcript_queue(self) -> TranscriptEvent | None:
        last_event: TranscriptEvent | None = None

        while not self._transcript_queue.empty():
            event = self._transcript_queue.get_nowait()
            last_event = event
            text = event.text.strip()
            if event.type == TranscriptType.FINAL and text:
                self._remember_final_segment(text)
            elif event.type == TranscriptType.PARTIAL and text:
                self._latest_partial = text

        final_text = self._combined_final_text()
        partial_text = self._latest_partial.strip()
        if final_text:
            return TranscriptEvent(text=final_text, type=TranscriptType.FINAL, language=self._language)
        if partial_text:
            return TranscriptEvent(text=partial_text, type=TranscriptType.PARTIAL, language=self._language)
        return last_event

    def _remember_final_segment(self, text: str) -> None:
        clean = text.strip()
        if not clean:
            return

        if not self._final_segments:
            self._final_segments.append(clean)
            return

        merged = self._merge_transcripts(self._combined_final_text(), clean)
        self._final_segments = [merged] if merged else []

    def _combined_final_text(self) -> str:
        return " ".join(segment.strip() for segment in self._final_segments if segment.strip()).strip()

    @classmethod
    def _merge_transcripts(cls, current: str, incoming: str) -> str:
        current = current.strip()
        incoming = incoming.strip()
        if not current:
            return incoming
        if not incoming:
            return current

        current_norm = cls._normalize_transcript(current)
        incoming_norm = cls._normalize_transcript(incoming)
        if current_norm == incoming_norm or incoming_norm in current_norm:
            return current
        if current_norm in incoming_norm:
            return incoming

        current_tokens = current_norm.split()
        incoming_tokens = incoming_norm.split()
        max_overlap = min(len(current_tokens), len(incoming_tokens))
        for overlap in range(max_overlap, 0, -1):
            if current_tokens[-overlap:] == incoming_tokens[:overlap]:
                incoming_words = incoming.split()
                return f"{current} {' '.join(incoming_words[overlap:])}".strip()

        return f"{current} {incoming}".strip()

    @staticmethod
    def _normalize_transcript(text: str) -> str:
        return re.sub(r"\s+", " ", re.sub(r"[^\w\s]", " ", text.lower())).strip()

    async def _shutdown_background_tasks(self) -> None:
        for task_name in ("_keepalive_task", "_receiver_task"):
            task = getattr(self, task_name)
            if task is None:
                continue
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                logger.debug("Deepgram ASR background task shutdown ignored: %s", exc)
            finally:
                setattr(self, task_name, None)

    async def _close_websocket(self, websocket: ClientConnection) -> None:
        try:
            await websocket.close()
        except Exception as exc:
            logger.debug("Deepgram ASR websocket close ignored: %s", exc)

    @staticmethod
    def _load_json(raw_message: str) -> dict[str, Any] | None:
        try:
            value = json.loads(raw_message)
        except json.JSONDecodeError:
            logger.debug("Deepgram ASR ignored non-JSON message: %s", raw_message[:200])
            return None
        if not isinstance(value, dict):
            return None
        return value

    def _extract_language(self, channel: Mapping[str, Any]) -> str:
        alternatives = channel.get("alternatives") or []
        if alternatives and isinstance(alternatives[0], Mapping):
            languages = alternatives[0].get("languages") or []
            if languages:
                return str(languages[0])
        return self._language

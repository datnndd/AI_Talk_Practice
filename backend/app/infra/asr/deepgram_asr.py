"""
Deepgram realtime ASR provider.

Streams PCM audio to Deepgram's Nova-3 WebSocket API and converts websocket
messages into the app's TranscriptEvent contract.
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import Mapping
from typing import Any
from urllib.parse import urlencode

from websockets.asyncio.client import ClientConnection, connect
from websockets.exceptions import ConnectionClosed

from app.core.config import Settings
from app.infra.contracts import ASRBase, TranscriptEvent, TranscriptType

logger = logging.getLogger(__name__)


class DeepgramASR(ASRBase):
    """Deepgram realtime ASR using the Nova-3 streaming model."""

    def __init__(self, config: Settings):
        self._config = config
        self._language = config.asr_language
        self._sample_rate = 16000
        self._websocket: ClientConnection | None = None
        self._transcript_queue: asyncio.Queue[TranscriptEvent] = asyncio.Queue()
        self._receiver_task: asyncio.Task | None = None
        self._keepalive_task: asyncio.Task | None = None
        self._connected = False

    async def start_session(self, language: str = "en", sample_rate: int = 16000) -> None:
        if self._connected:
            await self.stop_session()

        if not self._config.deepgram_api_key:
            raise ValueError("Deepgram ASR requires DEEPGRAM_API_KEY")

        self._language = language
        self._sample_rate = sample_rate
        self._transcript_queue = asyncio.Queue()

        query = urlencode(
            {
                "model": self._config.deepgram_asr_model,
                "language": language,
                "encoding": "linear16",
                "sample_rate": sample_rate,
                "interim_results": "true",
                "vad_events": "true",
                "endpointing": str(self._config.deepgram_endpointing_ms),
                "utterance_end_ms": str(self._config.deepgram_utterance_end_ms),
                "smart_format": "true",
                "punctuate": "true",
            }
        )
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
            "Deepgram ASR session started (model=%s, language=%s, rate=%s)",
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
            await asyncio.sleep(0.35)
            await websocket.send(json.dumps({"type": "CloseStream"}))
        except Exception as exc:
            logger.debug("Deepgram ASR finalize/close command failed: %s", exc)

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
                    continue
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

        if message_type == "Results":
            channel = payload.get("channel") or {}
            alternatives = channel.get("alternatives") or []
            transcript = ""
            if alternatives and isinstance(alternatives[0], Mapping):
                transcript = str(alternatives[0].get("transcript") or "").strip()
            language = self._extract_language(channel)

            if transcript:
                event_type = TranscriptType.FINAL if bool(payload.get("is_final")) else TranscriptType.PARTIAL
                self._transcript_queue.put_nowait(
                    TranscriptEvent(
                        text=transcript,
                        type=event_type,
                        language=language,
                    )
                )

            if bool(payload.get("speech_final")):
                self._transcript_queue.put_nowait(
                    TranscriptEvent(
                        text="",
                        type=TranscriptType.SPEECH_END,
                        language=language,
                    )
                )
            return

        if message_type == "UtteranceEnd":
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

    def _drain_transcript_queue(self) -> TranscriptEvent | None:
        last_event: TranscriptEvent | None = None
        final_text = ""
        partial_text = ""

        while not self._transcript_queue.empty():
            event = self._transcript_queue.get_nowait()
            last_event = event
            text = event.text.strip()
            if event.type == TranscriptType.FINAL and text:
                if not final_text:
                    final_text = text
                elif text == final_text or text in final_text:
                    continue
                elif final_text in text:
                    final_text = text
                else:
                    final_text = f"{final_text} {text}".strip()
            elif event.type == TranscriptType.PARTIAL and text:
                partial_text = text

        if final_text:
            return TranscriptEvent(text=final_text, type=TranscriptType.FINAL, language=self._language)
        if partial_text:
            return TranscriptEvent(text=partial_text, type=TranscriptType.PARTIAL, language=self._language)
        return last_event

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

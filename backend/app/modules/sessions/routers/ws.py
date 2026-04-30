"""WebSocket realtime endpoint router."""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import uuid
from contextlib import suppress
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.infra.factory import ConversationLLMClients, create_conversation_llm_clients, create_llm
from app.modules.sessions.schemas.session import MessageCreate, RealtimeCorrectionRequest, SessionCreate
from app.modules.sessions.serializers import get_session_character_payload
from app.modules.auth.services.auth_service import AuthService
from app.modules.sessions.services.conversation import ConversationSession
from app.modules.sessions.services.conversation_support import (
    ConversationEndingService,
    ConversationReplyService,
    ConversationSummaryService,
)
from app.modules.sessions.services.session import SessionService

logger = logging.getLogger(__name__)
conversation_logger = logging.getLogger("conversation_trace")

router = APIRouter()

_PENDING_RESUME_FINALIZE_TASKS: dict[int, asyncio.Task] = {}
_DEFAULT_CREATE_LLM = create_llm

NO_INPUT_MESSAGE = "Mải mê nghe giọng bạn làm mình đãng trí. Bạn có thể nói lại một lần nữa được không?"
TIME_LIMIT_MESSAGE = "Đã hết thời gian luyện tập. Mình sẽ chuyển bạn sang phần đánh giá."
NATURAL_CLOSE_MESSAGE = "Cuộc hội thoại đã khép lại. Bạn có thể xem phần phân tích khi sẵn sàng."
NATURAL_CLOSE_INSTRUCTION = "Trả lời lịch sự, khép lại cuộc trò chuyện một cách tự nhiên"


def _clip_log_text(value: str | None, *, limit: int = 500) -> str:
    text = " ".join((value or "").split())
    if len(text) <= limit:
        return text
    return f"{text[:limit]}... [truncated len={len(text)}]"


def _result_url(session_id: int) -> str:
    return f"/sessions/{session_id}/result"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _create_conversation_llm_clients() -> ConversationLLMClients:
    if create_llm is not _DEFAULT_CREATE_LLM:
        llm = create_llm(settings)
        return ConversationLLMClients(analysis=llm, dialogue=llm, evaluation=llm)
    return create_conversation_llm_clients(settings)


def _remaining_session_seconds(started_at: datetime, max_duration_seconds: int | None) -> float | None:
    if not max_duration_seconds or max_duration_seconds <= 0:
        return None
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    elapsed = (_utcnow() - started_at).total_seconds()
    return max(0.0, float(max_duration_seconds) - elapsed)


@router.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    await websocket.accept()
    connection_id = uuid.uuid4().hex[:10]
    logger.info("WebSocket connection accepted")
    conversation_logger.info("conn=%s event=websocket_accepted", connection_id)

    conversation: ConversationSession | None = None
    session_id: int | None = None
    finalized_user_messages = 0
    resume_enabled = False
    finalized_by_server = False
    timeout_task: asyncio.Task | None = None
    db_lock = asyncio.Lock()
    runtime_llm_clients: ConversationLLMClients | None = None
    reply_service: ConversationReplyService | None = None
    summary_service: ConversationSummaryService | None = None
    ending_service: ConversationEndingService | None = None
    pending_natural_close = False
    assistant_stream_chunk_count = 0
    assistant_stream_chars = 0
    audio_stream_chunk_count = 0
    audio_stream_bytes = 0

    def trace(event: str, **fields) -> None:
        base_fields = {
            "conn": connection_id,
            "session_id": session_id,
            "user_id": active_user_id,
            **fields,
        }
        details = " ".join(f"{key}={value!r}" for key, value in base_fields.items() if value is not None)
        conversation_logger.info("event=%s %s", event, details)

    async def send_json_safe(data: dict):
        try:
            state = getattr(websocket, "client_state", None)
            if state is None or getattr(state, "name", "CONNECTED") == "CONNECTED":
                await websocket.send_json(data)
        except Exception:
            logger.exception("Error sending WebSocket message")
            trace("websocket_send_error", payload_type=data.get("type"))

    async def on_transcript(text: str, transcript_type: str, metadata: dict | None = None):
        payload = {"type": f"transcript_{transcript_type}", "text": text}
        if metadata:
            payload.update(metadata)
        trace(
            "transcript",
            transcript_type=transcript_type,
            text_len=len(text or ""),
            text=_clip_log_text(text),
            message_id=payload.get("message_id"),
        )
        await send_json_safe(payload)

    async def on_llm_chunk(text: str, is_done: bool):
        nonlocal assistant_stream_chunk_count, assistant_stream_chars
        if is_done:
            trace(
                "assistant_done",
                chunk_count=assistant_stream_chunk_count,
                streamed_chars=assistant_stream_chars,
                final_chars=len(text or ""),
                text=_clip_log_text(text),
            )
            assistant_stream_chunk_count = 0
            assistant_stream_chars = 0
        else:
            assistant_stream_chunk_count += 1
            assistant_stream_chars += len(text or "")
            if assistant_stream_chunk_count == 1 or assistant_stream_chunk_count % 20 == 0:
                trace(
                    "assistant_chunk",
                    chunk_count=assistant_stream_chunk_count,
                    streamed_chars=assistant_stream_chars,
                    chunk_chars=len(text or ""),
                    text=_clip_log_text(text, limit=160),
                )
        await send_json_safe({"type": "llm_done" if is_done else "llm_chunk", "text": text})

    async def on_audio_chunk(audio_bytes: bytes | None):
        nonlocal audio_stream_chunk_count, audio_stream_bytes
        if audio_bytes is None:
            trace(
                "audio_done",
                chunk_count=audio_stream_chunk_count,
                audio_bytes=audio_stream_bytes,
            )
            audio_stream_chunk_count = 0
            audio_stream_bytes = 0
            await send_json_safe({"type": "audio_done"})
            return
        audio_stream_chunk_count += 1
        audio_stream_bytes += len(audio_bytes)
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        await send_json_safe({"type": "audio_chunk", "data": audio_b64})

    async def on_error(message: str):
        trace("pipeline_error", message=message)
        await send_json_safe({"type": "error", "message": message})

    async def on_no_input(reason: str, metrics: dict):
        trace("asr_no_input", reason=reason, metrics=metrics)
        await send_json_safe(
            {
                "type": "asr_no_input",
                "message": NO_INPUT_MESSAGE,
                "reason": reason,
                "metrics": metrics,
            }
        )

    async def persist_message(role: str, content: str):
        nonlocal finalized_user_messages, pending_natural_close
        if not session_id or not content.strip():
            return None
        try:
            trace(
                "persist_message_start",
                role=role,
                text_len=len(content or ""),
                text=_clip_log_text(content),
            )
            async with db_lock:
                async with AsyncSessionLocal() as db_write:
                    message = await SessionService.add_message(
                        db_write,
                        session_id=session_id,
                        user_id=active_user_id,
                        payload=SessionServiceMessageFactory.create(role=role, content=content.strip()),
                    )
                    await db_write.commit()
                    if role == "user":
                        finalized_user_messages += 1
                        session_for_summary = await SessionService.get_by_id(
                            db_write,
                            session_id,
                            active_user_id,
                        )
                        if summary_service and summary_service.should_summarize(session_for_summary):
                            summary = await summary_service.summarize(session=session_for_summary)
                            metadata = dict(session_for_summary.session_metadata or {})
                            metadata["rolling_summary"] = summary
                            metadata["conversation_engine"] = "realtime_v1"
                            session_for_summary.session_metadata = metadata
                            await db_write.commit()
                        if (
                            ending_service
                            and not pending_natural_close
                            and ending_service.should_consider(session=session_for_summary, user_text=message.content)
                        ):
                            pending_natural_close = await ending_service.should_end(session=session_for_summary)
                            trace("natural_close_decision", should_close=pending_natural_close)
                        asyncio.create_task(_emit_realtime_correction(message.id, message.content))
                    trace(
                        "persist_message_done",
                        role=role,
                        message_id=message.id,
                        order_index=message.order_index,
                    )
                    return {"message_id": message.id, "order_index": message.order_index}
        except Exception:
            logger.exception("Failed to persist websocket message")
            trace("persist_message_error", role=role, text_len=len(content or ""))
        return None

    async def _emit_realtime_correction(message_id: int, text: str) -> None:
        if session_id is None or active_user_id is None:
            return
        try:
            async with AsyncSessionLocal() as db_correction:
                response = await SessionService.correct_realtime(
                    db_correction,
                    session_id=session_id,
                    user_id=active_user_id,
                    payload=RealtimeCorrectionRequest(message_id=message_id, text=text),
                )
            await send_json_safe(
                {
                    "type": "message_correction",
                    "message_id": message_id,
                    "corrected_text": response.corrected_text,
                    "corrections": [item.model_dump(mode="json") for item in response.corrections],
                    "persisted": response.persisted,
                }
            )
        except Exception:
            logger.exception("Failed to emit realtime correction for message id=%s", message_id)

    active_user_id: int | None = None

    async def finalize_session(reason: str, *, metadata: dict | None = None) -> None:
        nonlocal finalized_by_server
        if session_id is None:
            return

        trace("finalize_session_start", reason=reason, metadata=metadata)
        finalized_by_server = True
        async with db_lock:
            async with AsyncSessionLocal() as db_final:
                finalized = await SessionService.finalize_after_ws_disconnect(
                    db_final,
                    session_id=session_id,
                    finalized_user_messages=finalized_user_messages,
                    metadata={"end_reason": reason, **(metadata or {})},
                )
        schedule_final_evaluation(session_id)

        status = finalized.status if finalized is not None else "completed"
        trace("finalize_session_done", reason=reason, status=status)
        await send_json_safe(
            {
                "type": "session_finalized",
                "session_id": session_id,
                "status": status,
                "reason": reason,
                "result_url": _result_url(session_id),
            }
        )

    async def run_timeout_after(seconds: float) -> None:
        try:
            await asyncio.sleep(seconds)
            trace("time_limit_reached", seconds=seconds)
            if conversation is not None:
                await conversation.cancel_recording()
                await conversation.interrupt_response()
            await send_json_safe(
                {
                    "type": "conversation_end",
                    "reason": "time_limit_reached",
                    "message": TIME_LIMIT_MESSAGE,
                }
            )
            await finalize_session("time_limit_reached")
            await websocket.close()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Error finalizing session after timeout")
            trace("time_limit_finalize_error")

    def schedule_final_evaluation(finalized_session_id: int) -> None:
        async def run() -> None:
            try:
                async with AsyncSessionLocal() as db_eval:
                    await SessionService.run_final_evaluation(db_eval, session_id=finalized_session_id)
                    await db_eval.commit()
            except Exception:
                logger.exception("Error running final evaluation for websocket session id=%s", finalized_session_id)

        asyncio.create_task(run())

    async def on_assistant_message_persist(text: str) -> None:
        nonlocal pending_natural_close
        await persist_message("assistant", text)
        if not pending_natural_close or finalized_by_server:
            return
        pending_natural_close = False
        trace("natural_close_start")
        await send_json_safe(
            {
                "type": "conversation_end",
                "session_id": session_id,
                "reason": "natural_close",
                "message": NATURAL_CLOSE_MESSAGE,
            }
        )
        await finalize_session(
            "natural_close",
            metadata={"conversation_closed_naturally": True},
        )
        await websocket.close()

    async def schedule_resume_finalize(user_message_count: int) -> None:
        if session_id is None:
            return

        resume_session_id = session_id

        async def delayed_finalize() -> None:
            try:
                await asyncio.sleep(max(0, settings.ws_resume_grace_seconds))
                async with AsyncSessionLocal() as db_final:
                    await SessionService.finalize_after_ws_disconnect(
                        db_final,
                        session_id=resume_session_id,
                        finalized_user_messages=user_message_count,
                        metadata={"end_reason": "websocket_disconnect"},
                    )
                    await db_final.commit()
                trace(
                    "resume_finalize_done",
                    resume_session_id=resume_session_id,
                    finalized_user_messages=user_message_count,
                )
                schedule_final_evaluation(resume_session_id)
            except asyncio.CancelledError:
                raise
            except Exception:
                logger.exception("Error finalizing websocket session id=%s after resume grace", resume_session_id)
                trace("resume_finalize_error", resume_session_id=resume_session_id)
            finally:
                task = _PENDING_RESUME_FINALIZE_TASKS.get(resume_session_id)
                if task is asyncio.current_task():
                    _PENDING_RESUME_FINALIZE_TASKS.pop(resume_session_id, None)

        previous = _PENDING_RESUME_FINALIZE_TASKS.pop(resume_session_id, None)
        if previous is not None and not previous.done():
            previous.cancel()

        trace("resume_finalize_scheduled", resume_session_id=resume_session_id, grace_seconds=settings.ws_resume_grace_seconds)
        _PENDING_RESUME_FINALIZE_TASKS[resume_session_id] = asyncio.create_task(delayed_finalize())

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                if not isinstance(msg, dict):
                    raise ValueError("Message must be a JSON object")
            except (json.JSONDecodeError, ValueError):
                trace("invalid_json")
                await send_json_safe({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")
            if msg_type and msg_type not in {"audio_chunk"}:
                trace("client_event", msg_type=msg_type)

            try:
                if msg_type == "session_start":
                    if conversation is not None:
                        trace("session_start_rejected", reason="already_started")
                        await send_json_safe({"type": "error", "message": "Session already started"})
                        continue

                    token = msg.get("token")
                    scenario_id = msg.get("scenario_id")
                    if not token or scenario_id is None:
                        trace("session_start_rejected", reason="missing_token_or_scenario")
                        await send_json_safe(
                            {"type": "error", "message": "session_start requires token and scenario_id"}
                        )
                        await websocket.close()
                        return

                    user_id = decode_token(token)
                    if user_id is None:
                        trace("session_start_rejected", reason="invalid_token")
                        await send_json_safe({"type": "error", "message": "Invalid token"})
                        await websocket.close()
                        return

                    request_metadata = dict(msg.get("metadata") or {})
                    request_metadata["conversation_engine"] = "realtime_v1"
                    resume_enabled = bool(request_metadata.get("resume_enabled"))
                    resume_session_id = msg.get("session_id")
                    is_resume = resume_session_id is not None

                    async with db_lock:
                        async with AsyncSessionLocal() as db_start:
                            user = await AuthService.get_user_by_id(db_start, user_id)
                            if user is None:
                                trace("session_start_rejected", reason="user_not_found")
                                await send_json_safe({"type": "error", "message": "User not found"})
                                await websocket.close()
                                return

                            if is_resume:
                                try:
                                    resume_session_id = int(resume_session_id)
                                except (TypeError, ValueError):
                                    trace("session_start_rejected", reason="invalid_session_id")
                                    await send_json_safe({"type": "error", "message": "Invalid session_id"})
                                    await websocket.close()
                                    return

                                session = await SessionService.get_by_id(db_start, resume_session_id, user.id)
                                if session.status != "active":
                                    trace("session_start_rejected", reason="inactive_session", resume_session_id=resume_session_id)
                                    await send_json_safe({"type": "error", "message": "Session is no longer active"})
                                    await websocket.close()
                                    return
                                if int(session.scenario_id) != int(scenario_id):
                                    trace("session_start_rejected", reason="scenario_mismatch", resume_session_id=resume_session_id)
                                    await send_json_safe({"type": "error", "message": "Session scenario mismatch"})
                                    await websocket.close()
                                    return
                            else:
                                session = await SessionService.start_session(
                                    db_start,
                                    user_id=user.id,
                                    user=user,
                                    payload=SessionCreate(
                                        scenario_id=scenario_id,
                                        metadata=request_metadata,
                                    ),
                                )
                    active_user_id = user.id
                    session_id = session.id
                    character_payload = get_session_character_payload(session) or {}
                    tts_voice = character_payload.get("tts_voice") or settings.tts_voice
                    asr_language = msg.get("language") or settings.asr_language
                    finalized_user_messages = len([item for item in session.messages if item.role == "user"])
                    trace(
                        "session_started",
                        scenario_id=session.scenario_id,
                        is_resume=is_resume,
                        finalized_user_messages=finalized_user_messages,
                        max_duration_seconds=session.scenario.estimated_duration,
                    )

                    pending_finalize = _PENDING_RESUME_FINALIZE_TASKS.pop(session.id, None)
                    if pending_finalize is not None and not pending_finalize.done():
                        pending_finalize.cancel()
                        trace("resume_finalize_cancelled")

                    runtime_llm_clients = _create_conversation_llm_clients()
                    reply_service = ConversationReplyService(
                        llm=runtime_llm_clients.dialogue,
                        message_limit=settings.llm_history_message_limit,
                    )
                    summary_service = ConversationSummaryService(
                        llm=runtime_llm_clients.analysis,
                        max_tokens=settings.analysis_llm_max_tokens or 400,
                        turn_interval=settings.conversation_summary_turn_interval,
                        summary_max_chars=settings.conversation_summary_max_chars,
                    )
                    ending_service = ConversationEndingService(
                        llm=runtime_llm_clients.analysis,
                        max_tokens=settings.analysis_llm_max_tokens or 250,
                        min_turns=6,
                    )

                    async def generate_reply_stream(_: str):
                        async with AsyncSessionLocal() as db_reply:
                            session_for_reply = await SessionService.get_by_id(
                                db_reply,
                                session.id,
                                user.id,
                            )
                        async for chunk in reply_service.stream_reply(
                            session=session_for_reply,
                            user_preferences=dict(user.preferences or {}),
                            extra_instruction=NATURAL_CLOSE_INSTRUCTION if pending_natural_close else None,
                        ):
                            yield chunk

                    conversation = ConversationSession(settings)
                    await conversation.initialize(
                        on_transcript=on_transcript,
                        on_llm_chunk=on_llm_chunk,
                        on_audio_chunk=on_audio_chunk,
                        on_error=on_error,
                        language=asr_language,
                        voice=tts_voice,
                        on_no_input=on_no_input,
                        on_user_message=lambda text: persist_message("user", text),
                        on_assistant_message=on_assistant_message_persist,
                        on_generate_reply_stream=generate_reply_stream,
                    )
                    max_duration_seconds = session.scenario.estimated_duration
                    remaining_seconds = _remaining_session_seconds(session.started_at, max_duration_seconds)
                    if remaining_seconds is not None:
                        if remaining_seconds <= 0:
                            timeout_task = asyncio.create_task(run_timeout_after(0))
                        else:
                            timeout_task = asyncio.create_task(run_timeout_after(remaining_seconds))

                    await send_json_safe(
                        {
                            "type": "session_started",
                            "session_id": session.id,
                            "scenario_id": session.scenario_id,
                            "language": asr_language,
                            "voice": tts_voice,
                            "character": character_payload,
                            "max_duration_seconds": max_duration_seconds,
                            "result_url": _result_url(session.id),
                        }
                    )

                    if conversation is not None and not is_resume:
                        intro_text = (session.scenario.description or "").strip()
                        if intro_text:
                            trace("opening_description_start", text_len=len(intro_text), text=_clip_log_text(intro_text))
                            await conversation.speak_opening(intro_text)
                        opening_reply = await reply_service.generate_opening_reply(
                            session=session,
                            user_preferences=dict(user.preferences or {}),
                        )
                        if opening_reply:
                            trace("opening_reply_start", text_len=len(opening_reply), text=_clip_log_text(opening_reply))
                            await conversation.speak_opening(opening_reply)
                    continue

                if conversation is None:
                    await send_json_safe(
                        {"type": "error", "message": "session_start is required before other events"}
                    )
                    continue

                if msg_type == "config":
                    active_language, active_voice = conversation.update_config(
                        language=msg.get("language"),
                        voice=None,
                    )
                    trace("config_updated", language=active_language, voice=active_voice)
                    await send_json_safe(
                        {"type": "config_updated", "language": active_language, "voice": active_voice}
                    )
                elif msg_type == "start_recording":
                    trace("recording_start_requested", language=msg.get("language"))
                    await conversation.start_recording(language=msg.get("language"))
                    await send_json_safe({"type": "recording_started"})
                elif msg_type == "stop_recording":
                    trace("recording_stop_requested")
                    await conversation.stop_recording()
                elif msg_type == "interrupt_assistant":
                    interrupted_text = await conversation.interrupt_response()
                    trace(
                        "assistant_interrupted",
                        text_len=len(interrupted_text or ""),
                        text=_clip_log_text(interrupted_text),
                    )
                    await send_json_safe({"type": "assistant_interrupted", "text": interrupted_text})
                elif msg_type == "audio_chunk":
                    audio_b64 = msg.get("data", "")
                    if not audio_b64:
                        continue
                    try:
                        await conversation.feed_audio(base64.b64decode(audio_b64))
                    except Exception:
                        trace("invalid_audio_data")
                        await send_json_safe({"type": "error", "message": "Invalid audio data"})
                else:
                    trace("unknown_client_event", msg_type=msg_type)
                    await send_json_safe({"type": "error", "message": f"Unknown message type: {msg_type}"})
            except AppError as exc:
                payload = {"type": "error", "message": exc.detail}
                if exc.extra:
                    payload["extra"] = exc.extra
                trace("app_error", msg_type=msg_type, detail=exc.detail, extra=exc.extra)
                await send_json_safe(payload)
                if msg_type == "session_start" and conversation is None:
                    await websocket.close()
                    return
            except Exception as exc:
                logger.exception("Error processing websocket event type=%s", msg_type)
                trace("event_processing_error", msg_type=msg_type, error=str(exc))
                await send_json_safe({"type": "error", "message": str(exc) if settings.is_debug else "Processing error"})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
        trace("websocket_disconnected")
    finally:
        trace("cleanup_start", finalized_by_server=finalized_by_server, resume_enabled=resume_enabled)
        if timeout_task is not None and not timeout_task.done():
            timeout_task.cancel()
            with suppress(asyncio.CancelledError):
                await timeout_task

        if conversation is not None:
            try:
                await conversation.close()
            except Exception:
                logger.exception("Error closing conversation")

        if runtime_llm_clients is not None:
            for client in {runtime_llm_clients.analysis, runtime_llm_clients.dialogue, runtime_llm_clients.evaluation}:
                try:
                    await client.close()
                except Exception:
                    logger.exception("Error closing realtime LLM client")

        if session_id is not None and not finalized_by_server:
            try:
                if resume_enabled:
                    trace("schedule_resume_finalize", finalized_user_messages=finalized_user_messages)
                    await schedule_resume_finalize(finalized_user_messages)
                else:
                    async with db_lock:
                        async with AsyncSessionLocal() as db_final:
                            await SessionService.finalize_after_ws_disconnect(
                                db_final,
                                session_id=session_id,
                                finalized_user_messages=finalized_user_messages,
                            )
                    trace("finalized_after_disconnect", finalized_user_messages=finalized_user_messages)
                    schedule_final_evaluation(session_id)
            except Exception:
                logger.exception("Error finalizing websocket session id=%s", session_id)
                trace("finalize_after_disconnect_error")

        logger.info("Session cleaned up")
        trace("cleanup_done")


class SessionServiceMessageFactory:
    @staticmethod
    def create(*, role: str, content: str) -> MessageCreate:
        return MessageCreate(role=role, content=content)

"""WebSocket realtime endpoint router."""

from __future__ import annotations

import asyncio
import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.modules.sessions.schemas.session import MessageCreate, SessionCreate
from app.modules.auth.services.auth_service import AuthService
from app.modules.sessions.services.lesson_runtime import LessonRuntimeService
from app.modules.sessions.services.conversation import ConversationSession
from app.modules.sessions.services.session import SessionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    conversation: ConversationSession | None = None
    session_id: int | None = None
    finalized_user_messages = 0
    lesson_engine_enabled = False
    db_lock = asyncio.Lock()

    async def send_json_safe(data: dict):
        try:
            state = getattr(websocket, "client_state", None)
            if state is None or getattr(state, "name", "CONNECTED") == "CONNECTED":
                await websocket.send_json(data)
        except Exception:
            logger.exception("Error sending WebSocket message")

    async def on_transcript(text: str, transcript_type: str):
        await send_json_safe({"type": f"transcript_{transcript_type}", "text": text})

    async def on_llm_chunk(text: str, is_done: bool):
        await send_json_safe({"type": "llm_done" if is_done else "llm_chunk", "text": text})

    async def on_audio_chunk(audio_bytes: bytes | None):
        if audio_bytes is None:
            await send_json_safe({"type": "audio_done"})
            return
        audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
        await send_json_safe({"type": "audio_chunk", "data": audio_b64})

    async def on_error(message: str):
        await send_json_safe({"type": "error", "message": message})

    async def persist_message(role: str, content: str):
        nonlocal finalized_user_messages
        if not session_id or not content.strip():
            return
        try:
            async with db_lock:
                async with AsyncSessionLocal() as db_write:
                    await SessionService.add_message(
                        db_write,
                        session_id=session_id,
                        user_id=active_user_id,
                        payload=SessionServiceMessageFactory.create(role=role, content=content.strip()),
                    )
            if role == "user":
                finalized_user_messages += 1
        except Exception:
            logger.exception("Failed to persist websocket message")

    async def send_lesson_state_event(state):
        payload = state.model_dump(mode="json")
        await send_json_safe({"type": "lesson_state", "lesson": payload})
        await send_json_safe({"type": "objective_progress", "progress": payload["progress"]})
        if state.should_end:
            await send_json_safe(
                {
                    "type": "conversation_end",
                    "reason": state.end_reason,
                    "message": state.completion_message,
                    "lesson": payload,
                }
            )

    active_user_id: int | None = None

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
                if not isinstance(msg, dict):
                    raise ValueError("Message must be a JSON object")
            except (json.JSONDecodeError, ValueError):
                await send_json_safe({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            try:
                if msg_type == "session_start":
                    if conversation is not None:
                        await send_json_safe({"type": "error", "message": "Session already started"})
                        continue

                    token = msg.get("token")
                    scenario_id = msg.get("scenario_id")
                    if not token or scenario_id is None:
                        await send_json_safe(
                            {"type": "error", "message": "session_start requires token and scenario_id"}
                        )
                        await websocket.close()
                        return

                    user_id = decode_token(token)
                    if user_id is None:
                        await send_json_safe({"type": "error", "message": "Invalid token"})
                        await websocket.close()
                        return

                    request_metadata = msg.get("metadata") or {}
                    async with db_lock:
                        async with AsyncSessionLocal() as db_start:
                            user = await AuthService.get_user_by_id(db_start, user_id)
                            if user is None:
                                await send_json_safe({"type": "error", "message": "User not found"})
                                await websocket.close()
                                return

                            session = await SessionService.start_session(
                                db_start,
                                user_id=user.id,
                                payload=SessionCreate(
                                    scenario_id=scenario_id,
                                    variation_id=msg.get("variation_id"),
                                    variation_seed=msg.get("variation_seed"),
                                    variation_parameters=msg.get("variation_parameters") or {},
                                    prefer_pregenerated=msg.get("prefer_pregenerated", True),
                                    create_variation_if_missing=msg.get("create_variation_if_missing", True),
                                    mode=msg.get("mode"),
                                    metadata=request_metadata,
                                    target_skills=msg.get("target_skills"),
                                ),
                            )
                    active_user_id = user.id
                    session_id = session.id
                    lesson_engine_enabled = request_metadata.get("conversation_engine") == "lesson_v1"

                    system_prompt = (
                        session.variation.system_prompt_override
                        if session.variation and session.variation.system_prompt_override
                        else session.scenario.ai_system_prompt
                    )

                    lesson_package = None
                    lesson_progress = None
                    lesson_hints = {}
                    if lesson_engine_enabled:
                        lesson_package, lesson_progress, lesson_hints = LessonRuntimeService.ensure_session_lesson(
                            scenario=session.scenario,
                            session_metadata=session.session_metadata,
                            level=user.level,
                        )
                        async with db_lock:
                            async with AsyncSessionLocal() as db_write:
                                session = await SessionService.merge_session_metadata(
                                    db_write,
                                    session_id=session.id,
                                    user_id=user.id,
                                    metadata={
                                        "lesson": LessonRuntimeService.serialize_lesson_metadata(
                                            package=lesson_package,
                                            state=lesson_progress,
                                            hints=lesson_hints,
                                        )
                                    },
                                )

                    async def generate_reply(text: str) -> str:
                        if not lesson_engine_enabled:
                            return ""

                        async with db_lock:
                            async with AsyncSessionLocal() as db_turn:
                                current_session = await SessionService.get_by_id(db_turn, session.id, user.id)
                        package, state, hints = LessonRuntimeService.deserialize_lesson_metadata(
                            current_session.session_metadata
                        )
                        result = LessonRuntimeService.advance(
                            scenario=current_session.scenario,
                            session_id=current_session.id,
                            package=package,
                            state=state,
                            user_answer=text,
                        )
                        async with db_lock:
                            async with AsyncSessionLocal() as db_write:
                                await SessionService.merge_session_metadata(
                                    db_write,
                                    session_id=current_session.id,
                                    user_id=user.id,
                                    metadata={
                                        "lesson": LessonRuntimeService.serialize_lesson_metadata(
                                            package=package,
                                            state=state,
                                            hints=hints,
                                        )
                                    },
                                )
                        await send_lesson_state_event(result.state)
                        return result.assistant_text

                    conversation = ConversationSession(settings)
                    await conversation.initialize(
                        on_transcript=on_transcript,
                        on_llm_chunk=on_llm_chunk,
                        on_audio_chunk=on_audio_chunk,
                        on_error=on_error,
                        system_prompt=system_prompt,
                        language=msg.get("language", settings.asr_language),
                        voice=msg.get("voice", settings.tts_voice),
                        on_user_message=lambda text: persist_message("user", text),
                        on_assistant_message=lambda text: persist_message("assistant", text),
                        on_generate_reply=generate_reply if lesson_engine_enabled else None,
                    )

                    await send_json_safe(
                        {
                            "type": "session_started",
                            "session_id": session.id,
                            "scenario_id": session.scenario_id,
                            "variation_id": session.variation_id,
                            "variation_seed": session.session_metadata.get("variation_seed"),
                            "mode": session.session_metadata.get("mode"),
                            "language": msg.get("language", settings.asr_language),
                            "voice": msg.get("voice", settings.tts_voice),
                        }
                    )

                    if lesson_engine_enabled and lesson_package and lesson_progress:
                        state = LessonRuntimeService.build_state_read(
                            session_id=session.id,
                            scenario=session.scenario,
                            package=lesson_package,
                            state=lesson_progress,
                        )
                        await send_json_safe({"type": "lesson_started", "lesson": state.model_dump(mode="json")})
                        await send_lesson_state_event(state)
                        await persist_message("assistant", state.current_question)
                    continue

                if conversation is None:
                    await send_json_safe(
                        {"type": "error", "message": "session_start is required before other events"}
                    )
                    continue

                if msg_type == "config":
                    active_language, active_voice = conversation.update_config(
                        language=msg.get("language"),
                        voice=msg.get("voice"),
                    )
                    await send_json_safe(
                        {"type": "config_updated", "language": active_language, "voice": active_voice}
                    )
                elif msg_type == "start_recording":
                    await conversation.start_recording(language=msg.get("language"))
                    await send_json_safe({"type": "recording_started"})
                elif msg_type == "stop_recording":
                    await conversation.stop_recording()
                elif msg_type == "interrupt_assistant":
                    interrupted_text = await conversation.interrupt_response()
                    await send_json_safe({"type": "assistant_interrupted", "text": interrupted_text})
                elif msg_type == "audio_chunk":
                    audio_b64 = msg.get("data", "")
                    if not audio_b64:
                        continue
                    try:
                        await conversation.feed_audio(base64.b64decode(audio_b64))
                    except Exception:
                        await send_json_safe({"type": "error", "message": "Invalid audio data"})
                else:
                    await send_json_safe({"type": "error", "message": f"Unknown message type: {msg_type}"})
            except AppError as exc:
                await send_json_safe({"type": "error", "message": exc.detail})
                if msg_type == "session_start" and conversation is None:
                    await websocket.close()
                    return
            except Exception as exc:
                logger.exception("Error processing websocket event type=%s", msg_type)
                await send_json_safe({"type": "error", "message": str(exc) if settings.is_debug else "Processing error"})
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    finally:
        if conversation is not None:
            try:
                await conversation.close()
            except Exception:
                logger.exception("Error closing conversation")

        if session_id is not None:
            try:
                async with db_lock:
                    async with AsyncSessionLocal() as db_final:
                        await SessionService.finalize_after_ws_disconnect(
                            db_final,
                            session_id=session_id,
                            finalized_user_messages=finalized_user_messages,
                        )
            except Exception:
                logger.exception("Error finalizing websocket session id=%s", session_id)

        logger.info("Session cleaned up")


class SessionServiceMessageFactory:
    @staticmethod
    def create(*, role: str, content: str) -> MessageCreate:
        return MessageCreate(role=role, content=content)

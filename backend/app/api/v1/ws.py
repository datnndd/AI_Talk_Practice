"""WebSocket realtime endpoint router."""

from __future__ import annotations

import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.core.exceptions import AppError
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.schemas.session import SessionCreate
from app.services.auth_service import AuthService
from app.services.conversation import ConversationSession
from app.services.session_service import SessionService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    async with AsyncSessionLocal() as db:
        conversation: ConversationSession | None = None
        session_id: int | None = None
        finalized_user_messages = 0

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
                await SessionService.add_message(
                    db,
                    session_id=session_id,
                    user_id=active_user_id,
                    payload=SessionServiceMessageFactory.create(role=role, content=content.strip()),
                )
                if role == "user":
                    finalized_user_messages += 1
            except Exception:
                logger.exception("Failed to persist websocket message")
                await db.rollback()

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

                        user = await AuthService.get_user_by_id(db, user_id)
                        if user is None:
                            await send_json_safe({"type": "error", "message": "User not found"})
                            await websocket.close()
                            return

                        active_user_id = user.id
                        session = await SessionService.start_session(
                            db,
                            user_id=user.id,
                            payload=SessionCreate(
                                scenario_id=scenario_id,
                                variation_id=msg.get("variation_id"),
                                variation_seed=msg.get("variation_seed"),
                                variation_parameters=msg.get("variation_parameters") or {},
                                prefer_pregenerated=msg.get("prefer_pregenerated", True),
                                create_variation_if_missing=msg.get("create_variation_if_missing", True),
                                mode=msg.get("mode"),
                                metadata=msg.get("metadata") or {},
                                target_skills=msg.get("target_skills"),
                            ),
                        )
                        session_id = session.id

                        system_prompt = (
                            session.variation.system_prompt_override
                            if session.variation and session.variation.system_prompt_override
                            else session.scenario.ai_system_prompt
                        )

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
                    await SessionService.finalize_after_ws_disconnect(
                        db,
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

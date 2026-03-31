"""
WebSocket realtime endpoint router.
"""

import base64
import json
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException

from app.core.config import settings
from app.core.security import decode_token
from app.db.session import AsyncSessionLocal
from app.models.message import Message
from app.models.session import Session
from app.services.scenario_service import ScenarioService
from app.services.auth_service import AuthService
from app.services.conversation import ConversationSession

logger = logging.getLogger(__name__)

router = APIRouter()

def _duration_seconds(started_at: datetime, ended_at: datetime) -> int:
    """Compute a non-negative session duration in seconds."""
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    return max(0, int((ended_at - started_at).total_seconds()))

@router.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    async with AsyncSessionLocal() as db:
        conversation: ConversationSession | None = None
        session_record: Session | None = None
        next_order_index = 1
        finalized_user_messages = 0

        async def send_json_safe(data: dict):
            try:
                state = getattr(websocket, "client_state", None)
                if state is None or getattr(state, "name", "CONNECTED") == "CONNECTED":
                    await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error sending WebSocket message: {e}")

        async def on_transcript(text: str, transcript_type: str):
            await send_json_safe({
                "type": f"transcript_{transcript_type}",
                "text": text,
            })

        async def on_llm_chunk(text: str, is_done: bool):
            if is_done:
                await send_json_safe({"type": "llm_done", "text": text})
            else:
                await send_json_safe({"type": "llm_chunk", "text": text})

        async def on_audio_chunk(audio_bytes: bytes | None):
            if audio_bytes is None:
                await send_json_safe({"type": "audio_done"})
            else:
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
                await send_json_safe({"type": "audio_chunk", "data": audio_b64})

        async def on_error(message: str):
            await send_json_safe({"type": "error", "message": message})

        async def persist_message(role: str, content: str):
            nonlocal next_order_index, finalized_user_messages
            if not session_record or not content.strip():
                return
            try:
                msg = Message(
                    session_id=session_record.id,
                    role=role,
                    content=content.strip(),
                    order_index=next_order_index,
                )
                db.add(msg)
                next_order_index += 1
                if role == "user":
                    finalized_user_messages += 1
                await db.commit()
            except Exception as e:
                logger.error(f"Failed to persist message: {e}")
                await db.rollback()

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

                        token = msg.get("token", "")
                        scenario_id = msg.get("scenario_id")
                        active_language = msg.get("language", settings.asr_language)
                        active_voice = msg.get("voice", settings.tts_voice)

                        if not token or scenario_id is None:
                            await send_json_safe({"type": "error", "message": "session_start requires token and scenario_id"})
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

                        try:
                            scenario = await ScenarioService.get_by_id(db, scenario_id)
                        except HTTPException as e:
                            await send_json_safe({"type": "error", "message": e.detail})
                            await websocket.close()
                            return

                        session_record = Session(
                            user_id=user.id,
                            scenario_id=scenario.id,
                            status="active",
                        )
                        db.add(session_record)
                        await db.commit()
                        await db.refresh(session_record)

                        conversation = ConversationSession(settings)
                        await conversation.initialize(
                            on_transcript=on_transcript,
                            on_llm_chunk=on_llm_chunk,
                            on_audio_chunk=on_audio_chunk,
                            on_error=on_error,
                            system_prompt=scenario.ai_system_prompt,
                            language=active_language,
                            voice=active_voice,
                            on_user_message=lambda text: persist_message("user", text),
                            on_assistant_message=lambda text: persist_message("assistant", text),
                        )

                        await send_json_safe({
                            "type": "session_started",
                            "session_id": session_record.id,
                            "scenario_id": scenario.id,
                            "language": active_language,
                            "voice": active_voice,
                        })
                        continue

                    if conversation is None:
                        await send_json_safe({"type": "error", "message": "session_start is required before other events"})
                        continue

                    if msg_type == "config":
                        active_language, active_voice = conversation.update_config(
                            language=msg.get("language"),
                            voice=msg.get("voice"),
                        )
                        await send_json_safe({
                            "type": "config_updated",
                            "language": active_language,
                            "voice": active_voice,
                        })

                    elif msg_type == "start_recording":
                        await conversation.start_recording(language=msg.get("language"))
                        await send_json_safe({"type": "recording_started"})

                    elif msg_type == "stop_recording":
                        await conversation.stop_recording()

                    elif msg_type == "audio_chunk":
                        audio_b64 = msg.get("data", "")
                        if audio_b64:
                            try:
                                audio_bytes = base64.b64decode(audio_b64)
                                await conversation.feed_audio(audio_bytes)
                            except Exception:
                                await send_json_safe({"type": "error", "message": "Invalid audio data"})

                    else:
                        await send_json_safe({"type": "error", "message": f"Unknown message type: {msg_type}"})

                except HTTPException as e:
                    await send_json_safe({"type": "error", "message": e.detail})
                except Exception as e:
                    logger.error(f"Error processing message {msg_type}: {e}", exc_info=True)
                    await send_json_safe({"type": "error", "message": "Generic processing error"})

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"Critical WebSocket error: {e}", exc_info=True)
        finally:
            if conversation:
                try:
                    await conversation.close()
                except Exception as e:
                    logger.error(f"Error closing conversation: {e}")

            if session_record:
                try:
                    ended_at = datetime.now(timezone.utc)
                    session_record.ended_at = ended_at
                    if finalized_user_messages > 0:
                        session_record.status = "completed"
                        session_record.duration_seconds = _duration_seconds(session_record.started_at, ended_at)
                    else:
                        session_record.status = "abandoned"
                        session_record.duration_seconds = None
                    await db.commit()
                except Exception as e:
                    logger.error(f"Error finalizing session record: {e}")

            logger.info("Session cleaned up")

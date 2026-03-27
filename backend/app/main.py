"""
FastAPI application with WebSocket endpoint for realtime AI conversation.

Pipeline: Microphone → ASR → LLM → TTS → Speaker
Communication: WebSocket with JSON + binary audio
"""

import base64
import json
import logging
import sys
from datetime import datetime, timezone

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select
from dotenv import load_dotenv

# Load .env before importing config
load_dotenv()

from app.auth import get_user_for_token
from app.config import settings
from app.conversation import ConversationSession
from app.database import AsyncSessionLocal, Base, engine
from app.models.message import Message
from app.models.scenario import Scenario
from app.models.session import Session
from app.routers import router as auth_router
from app.routers.scenarios import router as scenario_router
from app.routers.sessions import router as session_router

# ─── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ─── FastAPI App ────────────────────────────────────────────────────────────

app = FastAPI(
    title="AI Talk Practice - Realtime Conversation API",
    description="Realtime AI conversation backend: ASR → LLM → TTS pipeline via WebSocket",
    version="1.0.0",
)

# CORS (allow frontend dev server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(scenario_router)
app.include_router(session_router)


# ─── Health Check ───────────────────────────────────────────────────────────

@app.get("/")
async def health_check():
    """Health check and configuration overview."""
    return {
        "status": "ok",
        "service": "AI Talk Practice - Realtime Conversation API",
        "providers": {
            "asr": settings.asr_provider,
            "llm": settings.llm_provider,
            "tts": settings.tts_provider,
        },
        "config": {
            "llm_model": settings.llm_model,
            "asr_language": settings.asr_language,
            "tts_voice": settings.tts_voice,
        },
    }


@app.get("/providers")
async def list_providers():
    """List available providers and current configuration."""
    return {
        "asr": {
            "current": settings.asr_provider,
            "available": ["dashscope", "faster_whisper"],
        },
        "llm": {
            "current": settings.llm_provider,
            "available": ["gemini", "openai"],
        },
        "tts": {
            "current": settings.tts_provider,
            "available": ["dashscope", "kokoro"],
        },
    }


def _duration_seconds(started_at: datetime, ended_at: datetime) -> int:
    """Compute a non-negative session duration in seconds."""
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    return max(0, int((ended_at - started_at).total_seconds()))


# ─── WebSocket Endpoint ────────────────────────────────────────────────────

@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    """
    Main WebSocket endpoint for realtime conversation.

    Protocol:
        Client → Server (JSON):
            {"type": "session_start", "token": "<jwt>", "scenario_id": 1, "language": "en", "voice": "Cherry"}
            {"type": "start_recording"}
            {"type": "stop_recording"}
            {"type": "audio_chunk", "data": "<base64 PCM 16kHz 16-bit mono>"}
            {"type": "config", "language": "en", "voice": "Cherry"}

        Server → Client (JSON):
            {"type": "session_started", "session_id": 1, "scenario_id": 1, "language": "en", "voice": "Cherry"}
            {"type": "transcript_partial", "text": "..."}
            {"type": "transcript_final", "text": "..."}
            {"type": "llm_chunk", "text": "..."}
            {"type": "llm_done", "text": "full response"}
            {"type": "audio_chunk", "data": "<base64 PCM 24kHz>"}
            {"type": "audio_done"}
            {"type": "error", "message": "..."}
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    async with AsyncSessionLocal() as db:
        conversation: ConversationSession | None = None
        session_record: Session | None = None
        active_language = settings.asr_language
        active_voice = settings.tts_voice
        next_order_index = 1
        finalized_user_messages = 0

        async def send_json_safe(data: dict):
            """Send JSON message, catching any connection errors."""
            try:
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

            db.add(Message(
                session_id=session_record.id,
                role=role,
                content=content.strip(),
                order_index=next_order_index,
            ))
            next_order_index += 1
            if role == "user":
                finalized_user_messages += 1
            await db.commit()

        try:
            while True:
                raw = await websocket.receive_text()
                try:
                    msg = json.loads(raw)
                except json.JSONDecodeError:
                    await send_json_safe({"type": "error", "message": "Invalid JSON"})
                    continue

                msg_type = msg.get("type", "")

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

                    user = await get_user_for_token(db, token)
                    if user is None:
                        await send_json_safe({"type": "error", "message": "Invalid token"})
                        await websocket.close()
                        return

                    result = await db.execute(
                        select(Scenario).where(
                            Scenario.id == scenario_id,
                            Scenario.is_active.is_(True),
                        )
                    )
                    scenario = result.scalar_one_or_none()
                    if scenario is None:
                        await send_json_safe({"type": "error", "message": "Scenario not found"})
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
                    logger.info(f"Config update: language={active_language}, voice={active_voice}")
                    await send_json_safe({
                        "type": "config_updated",
                        "language": active_language,
                        "voice": active_voice,
                    })

                elif msg_type == "start_recording":
                    active_language, active_voice = conversation.update_config(
                        language=msg.get("language"),
                        voice=msg.get("voice"),
                    )
                    await conversation.start_recording(language=active_language)
                    await send_json_safe({"type": "recording_started"})

                elif msg_type == "stop_recording":
                    await conversation.stop_recording()

                elif msg_type == "audio_chunk":
                    audio_b64 = msg.get("data", "")
                    if audio_b64:
                        try:
                            audio_bytes = base64.b64decode(audio_b64)
                        except Exception:
                            await send_json_safe({"type": "error", "message": "Invalid audio chunk"})
                            continue
                        await conversation.feed_audio(audio_bytes)

                else:
                    logger.warning(f"Unknown message type: {msg_type}")
                    await send_json_safe({"type": "error", "message": f"Unknown message type: {msg_type}"})

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            await send_json_safe({"type": "error", "message": "Unexpected server error"})
        finally:
            if conversation:
                await conversation.close()

            if session_record:
                ended_at = datetime.now(timezone.utc)
                session_record.ended_at = ended_at
                if finalized_user_messages > 0:
                    session_record.status = "completed"
                    session_record.duration_seconds = _duration_seconds(session_record.started_at, ended_at)
                else:
                    session_record.status = "abandoned"
                    session_record.duration_seconds = None
                await db.commit()

            logger.info("Session cleaned up")


# ─── Startup ────────────────────────────────────────────────────────────────

@app.on_event("startup")
async def startup_event():
    # Import models so Base.metadata knows about all tables
    import app.models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified")

    logger.info("=" * 60)
    logger.info("AI Talk Practice - Realtime Conversation API")
    logger.info("=" * 60)
    logger.info(f"ASR Provider: {settings.asr_provider}")
    logger.info(f"LLM Provider: {settings.llm_provider} ({settings.llm_model})")
    logger.info(f"TTS Provider: {settings.tts_provider}")
    logger.info(f"DashScope Region: {settings.dashscope_region}")
    logger.info("=" * 60)


# ─── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )

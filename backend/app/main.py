"""
FastAPI application with WebSocket endpoint for realtime AI conversation.

Pipeline: Microphone → ASR → LLM → TTS → Speaker
Communication: WebSocket with JSON + binary audio
"""

import asyncio
import base64
import json
import logging
import os
import sys

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env before importing config
load_dotenv()

from app.config import settings
from app.conversation import ConversationSession
from app.database import engine, Base
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


# ─── WebSocket Endpoint ────────────────────────────────────────────────────

@app.websocket("/ws/conversation")
async def websocket_conversation(websocket: WebSocket):
    """
    Main WebSocket endpoint for realtime conversation.

    Protocol:
        Client → Server (JSON):
            {"type": "audio_chunk", "data": "<base64 PCM 16kHz 16-bit mono>"}
            {"type": "start_recording"}
            {"type": "stop_recording"}
            {"type": "config", "language": "en", "voice": "Cherry"}

        Server → Client (JSON):
            {"type": "transcript_partial", "text": "..."}
            {"type": "transcript_final", "text": "..."}
            {"type": "llm_chunk", "text": "..."}
            {"type": "llm_done", "text": "full response"}
            {"type": "audio_chunk", "data": "<base64 PCM 24kHz>"}
            {"type": "audio_done"}
            {"type": "error", "message": "..."}
            {"type": "ready"}
    """
    await websocket.accept()
    logger.info("WebSocket connection accepted")

    session = ConversationSession(settings)

    # ── Helper functions to send events back to client ──

    async def send_json_safe(data: dict):
        """Send JSON message, catching any connection errors."""
        try:
            await websocket.send_json(data)
        except Exception as e:
            logger.error(f"Error sending WebSocket message: {e}")

    async def on_transcript(text: str, type: str):
        await send_json_safe({
            "type": f"transcript_{type}",
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

    # ── Initialize session ──

    try:
        await session.initialize(
            on_transcript=on_transcript,
            on_llm_chunk=on_llm_chunk,
            on_audio_chunk=on_audio_chunk,
            on_error=on_error,
        )
        await send_json_safe({"type": "ready"})
    except Exception as e:
        logger.error(f"Failed to initialize session: {e}")
        await send_json_safe({"type": "error", "message": f"Initialization failed: {e}"})
        await websocket.close()
        return

    # ── Message loop ──

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await send_json_safe({"type": "error", "message": "Invalid JSON"})
                continue

            msg_type = msg.get("type", "")

            if msg_type == "config":
                # Update session configuration
                language = msg.get("language", settings.asr_language)
                voice = msg.get("voice", settings.tts_voice)
                logger.info(f"Config update: language={language}, voice={voice}")
                await send_json_safe({
                    "type": "config_updated",
                    "language": language,
                    "voice": voice,
                })

            elif msg_type == "start_recording":
                language = msg.get("language", settings.asr_language)
                await session.start_recording(language=language)
                await send_json_safe({"type": "recording_started"})

            elif msg_type == "stop_recording":
                await session.stop_recording()

            elif msg_type == "audio_chunk":
                audio_b64 = msg.get("data", "")
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    await session.feed_audio(audio_bytes)

            else:
                logger.warning(f"Unknown message type: {msg_type}")

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await session.close()
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

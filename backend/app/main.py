import logging
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env before importing config
load_dotenv()

# Register fully all models before routers or repositories trigger mapper initialization
import app.db.models  # noqa: F401

from app.api.router import api_router, ws_router
from app.core.config import settings
from app.core.exceptions import setup_exception_handlers
from app.db.session import engine
from app.db.base_class import Base

# ─── Logging ────────────────────────────────────────────────────────────────


class SuppressDashScopeWebSocketNoise(logging.Filter):
    """Hide noisy websocket-client shutdown logs emitted during normal DashScope teardown."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        if "Connection to remote host was lost" not in message:
            return True
        if "websocket closed due to Connection to remote host was lost" in message:
            return False
        if "error from callback" in message:
            return False
        if message.strip() in {
            "Connection to remote host was lost.",
            "Connection to remote host was lost. - goodbye",
        }:
            return False
        return True


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logging.getLogger("websocket").addFilter(SuppressDashScopeWebSocketNoise())
logger = logging.getLogger(__name__)

# ─── Lifespan ──────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create tables
    # async with engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)
    # logger.info("Database tables verified")
    
    logger.info("=" * 60)
    logger.info("AI Talk Practice - Realtime Conversation API")
    logger.info("=" * 60)
    logger.info(f"ASR Provider: {settings.asr_provider}")
    logger.info(f"LLM Provider: {settings.llm_provider} ({settings.llm_model})")
    logger.info(f"TTS Provider: {settings.tts_provider}")
    logger.info(f"DashScope Region: {settings.dashscope_region}")
    logger.info("=" * 60)

    yield
    
    # Shutdown logic if any
    logger.info("Application shutting down")

# ─── FastAPI App ────────────────────────────────────────────────────────────

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.rate_limit import limiter

app = FastAPI(
    title="AI Talk Practice - Realtime Conversation API",
    description="Realtime AI conversation backend: ASR → LLM → TTS pipeline via WebSocket",
    version="1.0.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Exception handlers
setup_exception_handlers(app)


# CORS configuration
# NOTE: allow_credentials=True requires explicit origins — wildcard "*" is rejected by browsers
_cors_origins = settings.cors_origins
if "*" in _cors_origins:
    # In development, include common localhost ports explicitly
    _cors_origins = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://localhost:8080",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routers
app.include_router(api_router, prefix="/api")
# WebSocket router is mounted at root level (no /api prefix)
# so the WS endpoint lives at ws://host/ws/conversation
app.include_router(ws_router)


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
            "available": ["openai"],
        },
        "tts": {
            "current": settings.tts_provider,
            "available": ["dashscope", "kokoro"],
        },
    }

# (Startup logic moved to lifespan)

# ─── Entry point ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )

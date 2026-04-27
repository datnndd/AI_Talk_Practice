import logging
import sys

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load .env before importing config
load_dotenv()

# Register fully all models before routers or repositories trigger mapper initialization
import app.db.models  # noqa: E402,F401

from app.api.router import api_router, ws_router  # noqa: E402
from app.core.config import settings  # noqa: E402
from app.core.exceptions import setup_exception_handlers  # noqa: E402

# ─── Logging ────────────────────────────────────────────────────────────────


class SuppressDashScopeWebSocketNoise(logging.Filter):
    """Hide noisy websocket-client shutdown logs emitted during normal DashScope teardown."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        expected_shutdown_fragments = (
            "Connection to remote host was lost",
            "Invalid close frame.",
        )
        if not any(fragment in message for fragment in expected_shutdown_fragments):
            return True
        if "websocket closed due to Connection to remote host was lost" in message:
            return False
        if "websocket closed due to Invalid close frame" in message:
            return False
        if "error from callback" in message:
            return False
        if message.strip() in {
            "Connection to remote host was lost.",
            "Connection to remote host was lost. - goodbye",
            "Invalid close frame.",
            "Invalid close frame. - goodbye",
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

from slowapi.errors import RateLimitExceeded  # noqa: E402
from slowapi import _rate_limit_exceeded_handler  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402

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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
            "deepgram_asr_model": settings.deepgram_asr_model,
            "tts_voice": settings.tts_voice,
        },
    }

@app.get("/providers")
async def list_providers():
    """List available providers and current configuration."""
    return {
        "asr": {
            "current": settings.asr_provider,
            "available": ["deepgram"],
        },
        "llm": {
            "current": settings.llm_provider,
            "available": ["openai"],
        },
        "tts": {
            "current": settings.tts_provider,
            "available": ["dashscope"],
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

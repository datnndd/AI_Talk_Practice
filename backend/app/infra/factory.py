"""
Provider factory: creates the appropriate service implementations based on config.

To add a new provider:
1. Implement the base class in services/asr/, llm/, or tts/
2. Add the import and mapping here
"""

import logging
from app.core.config import Settings
from app.services.base import ASRBase, LLMBase, TTSBase

logger = logging.getLogger(__name__)


def create_asr(config: Settings) -> ASRBase:
    """Create an ASR provider instance based on configuration."""
    provider = config.asr_provider.lower()

    if provider == "dashscope":
        from app.infra.asr.dashscope_asr import DashScopeASR
        logger.info("Using DashScope ASR (cloud API)")
        return DashScopeASR(config)

    elif provider == "faster_whisper":
        from app.infra.asr.faster_whisper_asr import FasterWhisperASR
        logger.info("Using faster-whisper ASR (local)")
        return FasterWhisperASR(config)

    else:
        raise ValueError(
            f"Unknown ASR provider: '{provider}'. "
            f"Available: dashscope, faster_whisper"
        )


def create_llm(config: Settings) -> LLMBase:
    """Create an LLM provider instance based on configuration."""
    provider = config.llm_provider.lower()

    if provider == "gemini":
        from app.infra.llm.gemini_llm import GeminiLLM
        logger.info("Using Gemini LLM")
        return GeminiLLM(config)

    elif provider == "openai":
        from app.infra.llm.openai_llm import OpenAILLM
        logger.info("Using OpenAI-compatible LLM")
        return OpenAILLM(config)

    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Available: gemini, openai"
        )


def create_tts(config: Settings) -> TTSBase:
    """Create a TTS provider instance based on configuration."""
    provider = config.tts_provider.lower()

    if provider == "dashscope":
        from app.infra.tts.dashscope_tts import DashScopeTTS
        logger.info("Using DashScope TTS (cloud API)")
        return DashScopeTTS(config)

    elif provider == "kokoro":
        from app.infra.tts.kokoro_tts import KokoroTTS
        logger.info("Using Kokoro TTS (local)")
        return KokoroTTS(config)

    else:
        raise ValueError(
            f"Unknown TTS provider: '{provider}'. "
            f"Available: dashscope, kokoro"
        )

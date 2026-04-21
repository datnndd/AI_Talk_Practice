"""
Provider factory: creates the appropriate service implementations based on config.

To add a new provider:
1. Implement the base class in services/asr/, llm/, or tts/
2. Add the import and mapping here
"""

import logging
from dataclasses import dataclass
from enum import Enum

from app.core.config import Settings
from app.infra.contracts import ASRBase, LLMBase, TTSBase

logger = logging.getLogger(__name__)


class LLMRole(str, Enum):
    ANALYSIS = "analysis"
    DIALOGUE = "dialogue"
    EVALUATION = "evaluation"


@dataclass(frozen=True)
class ConversationLLMClients:
    analysis: LLMBase
    dialogue: LLMBase
    evaluation: LLMBase


def create_asr(config: Settings) -> ASRBase:
    """Create an ASR provider instance based on configuration."""
    provider = config.asr_provider.lower()

    if provider == "deepgram":
        from app.infra.asr.dashscope_asr import DashScopeASR
        from app.infra.asr.deepgram_asr import DeepgramASR
        from app.infra.asr.failover_asr import FailoverASR
        logger.info("Using Deepgram ASR (primary) with DashScope ASR fallback")
        return FailoverASR(
            primary=DeepgramASR(config),
            secondary=DashScopeASR(config),
            primary_name="deepgram",
            secondary_name="dashscope",
        )

    if provider == "dashscope":
        from app.infra.asr.dashscope_asr import DashScopeASR
        logger.info("Using DashScope ASR (cloud API)")
        return DashScopeASR(config)

    raise ValueError(
        f"Unknown ASR provider: '{provider}'. "
        f"Available: deepgram, dashscope"
    )


def create_llm(config: Settings) -> LLMBase:
    """Create an LLM provider instance based on configuration."""
    provider = config.llm_provider.strip().lower()

    if provider == "openai":
        from app.infra.llm.openai_llm import OpenAILLM
        logger.info("Using OpenAI-compatible LLM")
        return OpenAILLM(config)

    else:
        raise ValueError(
            f"Unknown LLM provider: '{provider}'. "
            f"Available: openai"
        )


def _role_override(config: Settings, role: LLMRole, field: str):
    return getattr(config, f"{role.value}_llm_{field}", None)


def _config_for_llm_role(config: Settings, role: LLMRole) -> Settings:
    provider = _role_override(config, role, "provider") or config.llm_provider
    model = _role_override(config, role, "model") or config.llm_model
    base_url = _role_override(config, role, "base_url") or config.llm_base_url
    api_key = _role_override(config, role, "api_key") or config.openai_api_key
    temperature = _role_override(config, role, "temperature")
    max_tokens = _role_override(config, role, "max_tokens")

    updates = {
        "llm_provider": provider,
        "llm_model": model,
        "llm_base_url": base_url,
        "openai_api_key": api_key,
    }
    if temperature is not None:
        updates["llm_temperature"] = temperature
    if max_tokens is not None:
        updates["llm_max_tokens"] = max_tokens
    return config.model_copy(update=updates)


def create_llm_for_role(config: Settings, role: LLMRole) -> LLMBase:
    """Create an LLM provider for a specific conversation role."""
    role_config = _config_for_llm_role(config, role)
    logger.info("Using %s LLM role (provider=%s, model=%s)", role.value, role_config.llm_provider, role_config.llm_model)
    return create_llm(role_config)


def create_conversation_llm_clients(config: Settings) -> ConversationLLMClients:
    """Create the analysis, dialogue, and final-evaluation LLM clients."""
    return ConversationLLMClients(
        analysis=create_llm_for_role(config, LLMRole.ANALYSIS),
        dialogue=create_llm_for_role(config, LLMRole.DIALOGUE),
        evaluation=create_llm_for_role(config, LLMRole.EVALUATION),
    )


def create_tts(config: Settings) -> TTSBase:
    """Create a TTS provider instance based on configuration."""
    provider = config.tts_provider.lower()

    if provider == "dashscope":
        from app.infra.tts.dashscope_tts import DashScopeTTS
        logger.info("Using DashScope TTS (cloud API)")
        return DashScopeTTS(config)

    raise ValueError(
        f"Unknown TTS provider: '{provider}'. "
        f"Available: dashscope"
    )

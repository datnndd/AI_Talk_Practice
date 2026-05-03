"""
Application configuration loaded from .env file.
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


DEFAULT_LLM_BASE_URL = "https://rfij5ml.9router.com/v1"


class Settings(BaseSettings):
    """Central configuration for all services. Loaded from .env file."""

    # --- Provider Selection ---
    asr_provider: str = Field(default="deepgram", description="ASR provider: deepgram")
    llm_provider: str = Field(default="openai", description="LLM provider: openai-compatible")
    tts_provider: str = Field(default="dashscope", description="TTS provider: dashscope")

    # --- Database ---
    database_url: str = Field(
        description="Async database connection URL",
    )

    # --- Auth / JWT ---
    jwt_secret_key: str = Field(default="change-me-in-production", description="JWT signing secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    jwt_expire_minutes: int = Field(default=1440, description="JWT token expiry in minutes (default 24h)")
    jwt_refresh_expire_minutes: int = Field(default=10080, description="JWT refresh token expiry in minutes (default 7d)")

    # --- OAuth ---
    google_client_id: Optional[str] = Field(default=None, description="Google OAuth Client ID")

    # --- SMTP / Email ---
    smtp_server: Optional[str] = Field(default=None, description="SMTP server address")
    smtp_port: int = Field(default=587, description="SMTP port")
    smtp_user: Optional[str] = Field(default=None, description="SMTP username")
    smtp_password: Optional[str] = Field(default=None, description="SMTP password")
    smtp_from_email: Optional[str] = Field(default="noreply@aitalkpractice.com", description="Sender email address")

    # --- API Keys ---
    dashscope_api_key: str | None = Field(default=None, description="DashScope API key")
    deepgram_api_key: str | None = Field(default=None, description="Deepgram API key")
    openai_api_key: str | None = Field(default=None, description="OpenAI-compatible LLM API key")
    stripe_secret_key: str | None = Field(default=None, description="Stripe secret key")
    stripe_webhook_secret: str | None = Field(default=None, description="Stripe webhook signing secret")
    google_translate_api_key: str | None = Field(default=None, description="Google Cloud Translation API v2 Key")
    azure_speech_key: str | None = Field(default=None, description="Azure Speech Service key")
    azure_speech_region: str | None = Field(default=None, description="Azure Speech Service region")
    azure_speech_language: str = Field(default="en-US", description="Azure Speech assessment language")
    dictionary_api_base_url: str = Field(
        default="https://dict.minhqnd.com",
        description="Public dictionary API base URL used for pronunciation audio",
    )
    lesson_audio_upload_max_bytes: int = Field(
        default=10 * 1024 * 1024,
        description="Maximum uploaded lesson audio size in bytes",
    )

    # --- Payment / Billing ---
    frontend_url: str = Field(description="Public frontend base URL")

    # --- LLM Configuration ---
    llm_model: str = Field(default="ai-talk", description="LLM model name")
    llm_base_url: str = Field(
        default=DEFAULT_LLM_BASE_URL,
        description="OpenAI-compatible LLM base URL",
    )
    llm_system_prompt: str = Field(
        default=(
            "You are a friendly and patient English conversation tutor. "
            "Help the user practice speaking English naturally. "
            "Keep responses concise (2-3 sentences). "
            "Correct major errors gently. Encourage the user to speak more."
        ),
        description="System prompt for the LLM",
    )
    llm_temperature: float = Field(default=0.3, description="Sampling temperature for LLM generation")
    llm_max_tokens: int = Field(default=800, description="Maximum tokens generated per assistant turn")
    lesson_plan_llm_max_tokens: int = Field(
        default=2400,
        description="Maximum tokens generated when creating structured lesson plans",
    )
    lesson_hint_llm_max_tokens: int = Field(
        default=700,
        description="Maximum tokens generated when creating structured lesson hints",
    )
    llm_history_message_limit: int = Field(
        default=6,
        description="How many recent conversation messages to send to the LLM",
    )

    # --- Role-specific LLM Configuration ---
    analysis_llm_provider: str | None = Field(default=None, description="LLM provider for turn analysis")
    analysis_llm_model: str | None = Field(default=None, description="LLM model for turn analysis")
    analysis_llm_base_url: str | None = Field(default=None, description="LLM base URL for turn analysis")
    analysis_llm_api_key: str | None = Field(default=None, description="LLM API key for turn analysis")
    analysis_llm_temperature: float | None = Field(default=None, description="LLM temperature for turn analysis")
    analysis_llm_max_tokens: int | None = Field(default=None, description="Maximum tokens for turn analysis")

    dialogue_llm_provider: str | None = Field(default=None, description="LLM provider for realtime dialogue")
    dialogue_llm_model: str | None = Field(default=None, description="LLM model for realtime dialogue")
    dialogue_llm_base_url: str | None = Field(default=None, description="LLM base URL for realtime dialogue")
    dialogue_llm_api_key: str | None = Field(default=None, description="LLM API key for realtime dialogue")
    dialogue_llm_temperature: float | None = Field(default=None, description="LLM temperature for realtime dialogue")
    dialogue_llm_max_tokens: int | None = Field(default=None, description="Maximum tokens for realtime dialogue")

    evaluation_llm_provider: str | None = Field(default=None, description="LLM provider for final session evaluation")
    evaluation_llm_model: str | None = Field(default=None, description="LLM model for final session evaluation")
    evaluation_llm_base_url: str | None = Field(default=None, description="LLM base URL for final session evaluation")
    evaluation_llm_api_key: str | None = Field(default=None, description="LLM API key for final session evaluation")
    evaluation_llm_temperature: float | None = Field(default=None, description="LLM temperature for final session evaluation")
    evaluation_llm_max_tokens: int | None = Field(default=None, description="Maximum tokens for final session evaluation")

    # --- Hybrid Conversation Orchestration ---
    conversation_memory_max_facts: int = Field(
        default=12,
        description="Maximum structured short-term facts retained per realtime conversation session",
    )
    conversation_recent_turn_limit: int = Field(
        default=6,
        description="Maximum compact recent turns retained in hybrid conversation memory",
    )
    conversation_summary_max_chars: int = Field(
        default=900,
        description="Maximum characters retained in the hybrid conversation rolling summary",
    )
    conversation_summary_turn_interval: int = Field(
        default=8,
        description="Summarize hybrid conversation memory after this many learner turns",
    )
    conversation_relevance_on_topic_threshold: float = Field(
        default=0.28,
        description="Rule-based relevance score required to treat a user turn as on-topic",
    )
    conversation_relevance_partial_threshold: float = Field(
        default=0.12,
        description="Rule-based relevance score required to treat a user turn as partially on-topic",
    )
    conversation_enable_llm_fact_extraction: bool = Field(
        default=True,
        description="Run LLM-based analysis and learner info collection before dialogue replies",
    )
    conversation_enable_llm_relevance_analysis: bool = Field(
        default=True,
        description="Use LLM-based relevance analysis before dialogue replies",
    )
    conversation_repair_max_repeats: int = Field(
        default=2,
        description="Maximum repeated repair attempts before narrowing the prompt more aggressively",
    )
    conversation_final_evaluation_timeout_seconds: float = Field(
        default=60.0,
        description="Best-effort timeout for final session evaluation LLM calls",
    )

    # --- ASR Configuration ---
    asr_language: str = Field(default="en", description="ASR language code")
    deepgram_asr_model: str = Field(default="flux-general-en", description="Deepgram Flux ASR model")
    deepgram_ws_url: str = Field(
        default="wss://api.deepgram.com/v2/listen",
        description="Deepgram Flux realtime speech-to-text WebSocket URL",
    )
    deepgram_eot_threshold: float = Field(
        default=0.7,
        description="Deepgram Flux end-of-turn confidence threshold",
    )
    deepgram_eot_timeout_ms: int = Field(
        default=1200,
        description="Deepgram Flux silence timeout before end-of-turn",
    )
    deepgram_endpointing_ms: int = Field(
        default=700,
        description="Deepgram endpointing pause threshold in milliseconds",
    )
    deepgram_utterance_end_ms: int = Field(
        default=1600,
        description="Deepgram utterance end threshold in milliseconds",
    )
    deepgram_keepalive_seconds: float = Field(
        default=3.0,
        description="Deepgram websocket keepalive interval while streaming",
    )
    asr_finalization_grace_ms: int = Field(
        default=1200,
        description="Delay after ASR speech-end/final events before closing the turn, so trailing audio can arrive",
    )
    asr_emit_partial_transcripts: bool = Field(
        default=True,
        description="Send interim ASR transcripts to clients while the user is speaking.",
    )
    asr_min_audio_ms: int = Field(
        default=200,
        description="Minimum recorded audio duration required before accepting a speech turn",
    )
    asr_min_rms: float = Field(
        default=0.003,
        description="Minimum PCM RMS level required before accepting a speech turn",
    )
    ws_resume_grace_seconds: int = Field(
        default=8,
        description="Seconds to keep a realtime session active after an unexpected websocket disconnect",
    )

    # --- TTS Configuration ---
    tts_model: str = Field(
        default="qwen3-tts-instruct-flash-realtime-2026-01-22",
        description="DashScope Qwen instruct TTS model",
    )
    tts_voice: str = Field(default="myvoice", description="DashScope Qwen TTS voice ID")
    tts_language: str = Field(default="en", description="TTS language")
    tts_instructions: str | None = Field(
        default="Speak in a natural, friendly English tutor voice with clear pronunciation.",
        description="Qwen instruct TTS speaking style instructions",
    )
    tts_optimize_instructions: bool = Field(
        default=True,
        description="Let Qwen instruct TTS optimize speaking style instructions",
    )
    # --- DashScope Region ---
    dashscope_region: str = Field(default="intl", description="intl | cn")

    # --- Server ---
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    is_debug: bool = Field(default=False)
    cors_origins: list[str] = Field(description="Allowed browser origins")

    @property
    def dashscope_ws_url(self) -> str:
        """WebSocket URL for DashScope realtime services."""
        if self.dashscope_region == "cn":
            return "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
        return "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"

    @property
    def llm_api_key(self) -> str | None:
        """Get the API key for the OpenAI-compatible LLM gateway."""
        return self.openai_api_key

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()

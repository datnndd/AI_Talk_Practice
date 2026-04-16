"""
Application configuration loaded from .env file.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Central configuration for all services. Loaded from .env file."""

    # --- Provider Selection ---
    asr_provider: str = Field(default="dashscope", description="ASR provider: dashscope | faster_whisper")
    llm_provider: str = Field(default="gemini", description="LLM provider: gemini | openai")
    tts_provider: str = Field(default="dashscope", description="TTS provider: dashscope | kokoro")

    # --- Database ---
    database_url: str = Field(
        default="sqlite+aiosqlite:///./ai_talk_practice.db",
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
    dashscope_api_key: Optional[str] = Field(default=None, description="DashScope API key")
    gemini_api_key: Optional[str] = Field(default=None, description="Gemini API key")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key (optional)")
    stripe_secret_key: Optional[str] = Field(default=None, description="Stripe secret key")
    stripe_webhook_secret: Optional[str] = Field(default=None, description="Stripe webhook signing secret")

    # --- Payment / Billing ---
    frontend_url: str = Field(default="http://localhost:5173", description="Public frontend base URL")
    payment_pro_duration_days: int = Field(default=30, description="Subscription duration in days after a successful payment")
    payment_pro_amount_usd_cents: int = Field(default=9900, description="Stripe price for PRO plan in cents")

    # --- LLM Configuration ---
    llm_model: str = Field(default="gemini-3.1-flash-lite-preview", description="LLM model name")
    llm_base_url: str = Field(
        default="https://generativelanguage.googleapis.com/v1beta/openai/",
        description="LLM OpenAI-compatible base URL",
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
    llm_max_tokens: int = Field(default=160, description="Maximum tokens generated per assistant turn")
    lesson_plan_llm_max_tokens: int = Field(
        default=1400,
        description="Maximum tokens generated when creating structured lesson plans",
    )
    llm_history_message_limit: int = Field(
        default=6,
        description="How many recent conversation messages to send to the LLM",
    )

    # --- ASR Configuration ---
    asr_language: str = Field(default="en", description="ASR language code")
    asr_model: str = Field(default="qwen3-asr-flash-realtime", description="DashScope ASR model")
    asr_model_local: str = Field(default="small", description="faster-whisper model size")
    asr_finalization_grace_ms: int = Field(
        default=700,
        description="Delay after ASR speech-end/final events before closing the turn, so trailing audio can arrive",
    )
    asr_emit_partial_transcripts: bool = Field(
        default=False,
        description="Send interim ASR transcripts to clients. Disabled by default to prioritize final accuracy.",
    )
    asr_beam_size: int = Field(default=8, description="Beam size for local faster-whisper final transcription")
    asr_best_of: int = Field(default=5, description="Best-of candidates for local faster-whisper transcription")

    # --- TTS Configuration ---
    tts_voice: str = Field(default="Cherry", description="DashScope TTS voice name")
    tts_language: str = Field(default="en", description="TTS language")
    tts_voice_local: str = Field(default="af_heart", description="Kokoro voice ID")

    # --- DashScope Region ---
    dashscope_region: str = Field(default="intl", description="intl | cn")

    # --- Server ---
    host: str = Field(default="0.0.0.0")
    port: int = Field(default=8000)
    is_debug: bool = Field(default=False)
    cors_origins: list[str] = Field(default=["*"])

    @property
    def dashscope_ws_url(self) -> str:
        """WebSocket URL for DashScope realtime services."""
        if self.dashscope_region == "cn":
            return "wss://dashscope.aliyuncs.com/api-ws/v1/realtime"
        return "wss://dashscope-intl.aliyuncs.com/api-ws/v1/realtime"

    @property
    def llm_api_key(self) -> Optional[str]:
        """Get the appropriate API key for the configured LLM provider."""
        if self.llm_provider == "gemini":
            return self.gemini_api_key
        if self.llm_provider == "openai":
            return self.openai_api_key
        return self.dashscope_api_key

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# Singleton settings instance
settings = Settings()

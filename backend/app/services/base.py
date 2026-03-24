"""
Abstract base classes defining the interface for ASR, LLM, and TTS services.

To add a new provider:
1. Create a new file in the appropriate services/ subdirectory
2. Implement the abstract methods from the base class
3. Register it in factory.py
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import AsyncGenerator, Optional


# ─── Data Models ────────────────────────────────────────────────────────────


class TranscriptType(str, Enum):
    PARTIAL = "partial"
    FINAL = "final"


@dataclass
class TranscriptEvent:
    """A transcript event from the ASR service."""
    text: str
    type: TranscriptType
    language: Optional[str] = None


@dataclass
class Message:
    """A chat message for LLM conversation history."""
    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class TTSConfig:
    """Configuration for a TTS synthesis request."""
    voice: str = "Cherry"
    language: str = "en"
    sample_rate: int = 24000


# ─── Abstract Base Classes ──────────────────────────────────────────────────


class ASRBase(ABC):
    """
    Abstract base class for Automatic Speech Recognition (ASR) services.

    Implementations should handle:
    - Opening/closing a streaming session
    - Receiving audio chunks and producing transcript events
    """

    @abstractmethod
    async def start_session(self, language: str = "en", sample_rate: int = 16000) -> None:
        """Initialize an ASR streaming session."""
        ...

    @abstractmethod
    async def feed_audio(self, audio_chunk: bytes) -> None:
        """Feed a chunk of audio data (PCM 16-bit mono) to the ASR engine."""
        ...

    @abstractmethod
    async def get_transcript(self) -> Optional[TranscriptEvent]:
        """
        Get next available transcript event (non-blocking).
        Returns None if no transcript is available yet.
        """
        ...

    @abstractmethod
    async def stop_session(self) -> Optional[TranscriptEvent]:
        """
        Stop the ASR session and return any remaining final transcript.
        """
        ...

    async def close(self) -> None:
        """Clean up resources. Override if needed."""
        pass


class LLMBase(ABC):
    """
    Abstract base class for Large Language Model (LLM) services.

    Implementations should handle:
    - Streaming chat completions
    - Managing conversation context
    """

    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a chat completion response token-by-token.

        Args:
            messages: Conversation history.
            system_prompt: Optional system prompt override.

        Yields:
            Text chunks as they're generated.
        """
        ...

    async def close(self) -> None:
        """Clean up resources. Override if needed."""
        pass


class TTSBase(ABC):
    """
    Abstract base class for Text-to-Speech (TTS) services.

    Implementations should handle:
    - Converting text (potentially streamed) to audio chunks
    - Streaming audio output as it's synthesized
    """

    @abstractmethod
    async def synthesize_stream(
        self,
        text_iterator: AsyncGenerator[str, None],
        config: Optional[TTSConfig] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Convert a stream of text chunks into a stream of audio chunks.

        Args:
            text_iterator: Async generator yielding text chunks.
            config: Optional TTS configuration.

        Yields:
            Audio chunks (PCM bytes).
        """
        ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        config: Optional[TTSConfig] = None,
    ) -> AsyncGenerator[bytes, None]:
        """
        Synthesize a complete text string into streamed audio chunks.

        Args:
            text: Complete text to synthesize.
            config: Optional TTS configuration.

        Yields:
            Audio chunks (PCM bytes).
        """
        ...

    async def close(self) -> None:
        """Clean up resources. Override if needed."""
        pass

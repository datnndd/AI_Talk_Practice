"""
Shared contracts and payload types for AI providers.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import AsyncGenerator


class TranscriptType(str, Enum):
    PARTIAL = "partial"
    FINAL = "final"


@dataclass
class TranscriptEvent:
    text: str
    type: TranscriptType
    language: str | None = None


@dataclass
class Message:
    role: str
    content: str


@dataclass
class TTSConfig:
    voice: str = "Cherry"
    language: str = "en"
    sample_rate: int = 24000


class ASRBase(ABC):
    @abstractmethod
    async def start_session(self, language: str = "en", sample_rate: int = 16000) -> None:
        ...

    @abstractmethod
    async def feed_audio(self, audio_chunk: bytes) -> None:
        ...

    @abstractmethod
    async def get_transcript(self) -> TranscriptEvent | None:
        ...

    @abstractmethod
    async def stop_session(self) -> TranscriptEvent | None:
        ...

    async def close(self) -> None:
        pass


class LLMBase(ABC):
    @abstractmethod
    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: str | None = None,
    ) -> AsyncGenerator[str, None]:
        ...

    async def close(self) -> None:
        pass


class TTSBase(ABC):
    @abstractmethod
    async def synthesize_stream(
        self,
        text_iterator: AsyncGenerator[str, None],
        config: TTSConfig | None = None,
    ) -> AsyncGenerator[bytes, None]:
        ...

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        config: TTSConfig | None = None,
    ) -> AsyncGenerator[bytes, None]:
        ...

    async def close(self) -> None:
        pass

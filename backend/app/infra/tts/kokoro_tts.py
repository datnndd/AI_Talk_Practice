"""
Local TTS provider using Kokoro.

Kokoro is a lightweight (82M params) TTS model that runs locally,
even on machines with limited VRAM (~0.3GB).
"""

import asyncio
import io
import logging
from typing import AsyncGenerator, Optional

import numpy as np

from app.core.config import Settings
from app.infra.contracts import TTSBase, TTSConfig

logger = logging.getLogger(__name__)


class KokoroTTS(TTSBase):
    """Local TTS using Kokoro (82M parameters)."""

    def __init__(self, config: Settings):
        self._config = config
        self._pipeline = None
        self._voice = config.tts_voice_local

    def _ensure_model(self):
        """Lazy-load the Kokoro model."""
        if self._pipeline is None:
            try:
                from kokoro import KPipeline
            except ImportError:
                raise ImportError(
                    "kokoro is not installed. "
                    "Install with: pip install -r requirements-local.txt"
                )

            lang_code = self._config.tts_language[:2] if self._config.tts_language else "a"
            logger.info(f"Loading Kokoro TTS pipeline (lang={lang_code})")
            self._pipeline = KPipeline(lang_code=lang_code)

    async def synthesize_stream(
        self,
        text_iterator: AsyncGenerator[str, None],
        config: Optional[TTSConfig] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Convert streamed text into streamed audio."""

        # Collect text chunks into sentences for better TTS quality
        text_buffer = ""
        sentence_endings = {".", "!", "?", "。", "！", "？", "\n"}

        async for text_chunk in text_iterator:
            text_buffer += text_chunk

            # Check if we have a complete sentence
            for i, char in enumerate(text_buffer):
                if char in sentence_endings:
                    sentence = text_buffer[: i + 1].strip()
                    text_buffer = text_buffer[i + 1 :]

                    if sentence:
                        async for audio_chunk in self.synthesize(sentence, config):
                            yield audio_chunk
                    break

        # Handle remaining text
        if text_buffer.strip():
            async for audio_chunk in self.synthesize(text_buffer.strip(), config):
                yield audio_chunk

    async def synthesize(
        self,
        text: str,
        config: Optional[TTSConfig] = None,
    ) -> AsyncGenerator[bytes, None]:
        """Synthesize complete text to streamed audio."""
        cfg = config or TTSConfig(
            voice=self._config.tts_voice_local,
            language=self._config.tts_language,
        )

        # Ensure model is loaded
        await asyncio.get_event_loop().run_in_executor(None, self._ensure_model)

        # Generate audio in executor
        audio_segments = await asyncio.get_event_loop().run_in_executor(
            None, self._generate, text, cfg.voice
        )

        # Yield audio segments as PCM bytes
        for segment in audio_segments:
            yield segment

    def _generate(self, text: str, voice: str) -> list[bytes]:
        """Generate audio from text (blocking, runs in executor)."""
        try:
            results = []
            generator = self._pipeline(
                text,
                voice=voice,
                speed=1.0,
            )

            for _, _, audio in generator:
                if audio is not None:
                    # Kokoro outputs float32 audio at 24kHz
                    # Convert to PCM 16-bit for consistency
                    if isinstance(audio, np.ndarray):
                        # Normalize and convert to int16
                        audio_int16 = (audio * 32767).clip(-32768, 32767).astype(np.int16)
                        results.append(audio_int16.tobytes())

            return results

        except Exception as e:
            logger.error(f"Kokoro TTS generation error: {e}")
            return []

    async def close(self) -> None:
        """Release model resources."""
        self._pipeline = None

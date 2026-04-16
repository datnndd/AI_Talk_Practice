"""
Local ASR provider using faster-whisper.

Runs Whisper models locally via CTranslate2 for fast inference.
Suitable for machines with limited VRAM (small model ~1GB).
"""

import asyncio
import logging
from typing import Optional

import numpy as np

from app.core.config import Settings
from app.infra.contracts import ASRBase, TranscriptEvent, TranscriptType

logger = logging.getLogger(__name__)


class FasterWhisperASR(ASRBase):
    """Local ASR using faster-whisper."""

    def __init__(self, config: Settings):
        self._config = config
        self._model = None
        self._audio_buffer = bytearray()
        self._sample_rate = 16000
        self._language = "en"
        self._is_active = False

    def _ensure_model(self):
        """Lazy-load the whisper model."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
            except ImportError:
                raise ImportError(
                    "faster-whisper is not installed. "
                    "Install with: pip install -r requirements-local.txt"
                )

            model_size = self._config.asr_model_local
            logger.info(f"Loading faster-whisper model: {model_size}")

            # Try GPU first, fall back to CPU
            try:
                self._model = WhisperModel(
                    model_size,
                    device="cuda",
                    compute_type="float16",
                )
                logger.info("faster-whisper: using CUDA")
            except Exception:
                logger.warning("faster-whisper: CUDA not available, falling back to CPU")
                self._model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                )

    async def start_session(self, language: str = "en", sample_rate: int = 16000) -> None:
        """Start a new ASR session."""
        self._language = language
        self._sample_rate = sample_rate
        self._audio_buffer = bytearray()
        self._is_active = True

        # Load model in background thread
        await asyncio.get_event_loop().run_in_executor(None, self._ensure_model)
        logger.info(f"faster-whisper ASR session started (language={language})")

    async def feed_audio(self, audio_chunk: bytes) -> None:
        """Accumulate audio chunks for processing."""
        if not self._is_active:
            return
        self._audio_buffer.extend(audio_chunk)

    async def get_transcript(self) -> Optional[TranscriptEvent]:
        """
        Keep buffering audio during the turn.

        The app is accuracy-first: local Whisper runs once on the completed
        utterance instead of repeatedly decoding partial audio while the user
        is still speaking.
        """
        return None

    async def stop_session(self) -> Optional[TranscriptEvent]:
        """Stop session and transcribe remaining audio."""
        if not self._is_active:
            return None

        self._is_active = False

        if len(self._audio_buffer) > 0 and self._model:
            audio_data = self._pcm_to_float32(bytes(self._audio_buffer))

            if np.sqrt(np.mean(audio_data ** 2)) > 0.005:
                transcript = await asyncio.get_event_loop().run_in_executor(
                    None, self._transcribe, audio_data
                )
                self._audio_buffer = bytearray()

                if transcript:
                    return TranscriptEvent(
                        text=transcript,
                        type=TranscriptType.FINAL,
                        language=self._language,
                    )

        self._audio_buffer = bytearray()
        return None

    def _transcribe(self, audio: np.ndarray) -> Optional[str]:
        """Run whisper transcription (blocking, runs in executor)."""
        try:
            segments, _info = self._model.transcribe(
                audio,
                language=self._language if self._language != "auto" else None,
                beam_size=self._config.asr_beam_size,
                best_of=self._config.asr_best_of,
                temperature=0,
                vad_filter=False,
            )

            text_parts = []
            for segment in segments:
                text_parts.append(segment.text.strip())

            result = " ".join(text_parts).strip()
            return result if result else None

        except Exception as e:
            logger.error(f"faster-whisper transcription error: {e}")
            return None

    @staticmethod
    def _pcm_to_float32(pcm_bytes: bytes) -> np.ndarray:
        """Convert PCM 16-bit mono bytes to float32 numpy array."""
        audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
        audio /= 32768.0  # Normalize to [-1, 1]
        return audio

    async def close(self) -> None:
        """Release model resources."""
        self._model = None
        self._audio_buffer = bytearray()
        self._is_active = False

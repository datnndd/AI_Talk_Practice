"""
ASR failover wrapper.

Uses a primary ASR provider first and falls back to a secondary provider by
replaying buffered audio if the primary provider raises during a live turn.
"""

from __future__ import annotations

import logging

from app.infra.contracts import ASRBase, TranscriptEvent

logger = logging.getLogger(__name__)


class FailoverASR(ASRBase):
    """ASR wrapper that retries a live turn on a secondary provider."""

    def __init__(self, *, primary: ASRBase, secondary: ASRBase, primary_name: str, secondary_name: str):
        self._primary = primary
        self._secondary = secondary
        self._primary_name = primary_name
        self._secondary_name = secondary_name
        self._active = primary
        self._using_fallback = False
        self._audio_buffer: list[bytes] = []
        self._language = "en"
        self._sample_rate = 16000

    async def start_session(self, language: str = "en", sample_rate: int = 16000) -> None:
        self._language = language
        self._sample_rate = sample_rate
        self._audio_buffer = []
        self._active = self._primary
        self._using_fallback = False
        try:
            await self._primary.start_session(language=language, sample_rate=sample_rate)
        except Exception as exc:
            await self._switch_to_fallback(exc)

    async def feed_audio(self, audio_chunk: bytes) -> None:
        self._audio_buffer.append(audio_chunk)
        try:
            await self._active.feed_audio(audio_chunk)
        except Exception as exc:
            await self._switch_to_fallback(exc)

    async def get_transcript(self) -> TranscriptEvent | None:
        try:
            return await self._active.get_transcript()
        except Exception as exc:
            await self._switch_to_fallback(exc)
            return await self._active.get_transcript()

    async def stop_session(self) -> TranscriptEvent | None:
        try:
            return await self._active.stop_session()
        except Exception as exc:
            await self._switch_to_fallback(exc)
            return await self._active.stop_session()

    async def close(self) -> None:
        errors: list[Exception] = []
        for provider in (self._primary, self._secondary):
            try:
                await provider.close()
            except Exception as exc:
                errors.append(exc)
        if errors:
            logger.debug("ASR close ignored %s provider errors", len(errors))

    async def _switch_to_fallback(self, exc: Exception) -> None:
        if self._using_fallback:
            raise exc

        logger.warning(
            "ASR provider '%s' failed, switching to '%s': %s",
            self._primary_name,
            self._secondary_name,
            exc,
        )
        self._using_fallback = True

        try:
            await self._primary.close()
        except Exception as close_exc:
            logger.debug("Primary ASR close after failure ignored: %s", close_exc)

        await self._secondary.start_session(language=self._language, sample_rate=self._sample_rate)
        self._active = self._secondary

        for chunk in self._audio_buffer:
            await self._secondary.feed_audio(chunk)

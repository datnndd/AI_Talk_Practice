"""
DashScope HTTP streaming TTS provider.

Uses Alibaba Cloud Model Studio Qwen TTS through the non-realtime
MultiModalConversation API while preserving the app's streaming contract.
"""

import asyncio
import base64
import logging
import re
from collections.abc import AsyncGenerator, Generator
from http import HTTPStatus
from typing import Any

import dashscope
from dashscope import MultiModalConversation

from app.core.config import Settings
from app.infra.contracts import TTSBase, TTSConfig

logger = logging.getLogger(__name__)

_SENTENCE_END_RE = re.compile(r"[.!?。！？]\s+$")
_MIN_STREAM_TEXT_CHARS = 80
_MAX_STREAM_TEXT_CHARS = 180

_LANGUAGE_TYPE_BY_CODE = {
    "en": "English",
    "en-us": "English",
    "en-gb": "English",
    "zh": "Chinese",
    "zh-cn": "Chinese",
    "zh-tw": "Chinese",
    "ja": "Japanese",
    "jp": "Japanese",
    "ko": "Korean",
}


def _language_type(language: str | None) -> str | None:
    if not language:
        return None
    normalized = language.strip().lower().replace("_", "-")
    return _LANGUAGE_TYPE_BY_CODE.get(normalized, language)


def _response_attr(response: Any, name: str) -> Any:
    if isinstance(response, dict):
        return response.get(name)
    return getattr(response, name, None)


def _extract_audio_bytes(response: Any) -> bytes:
    output = _response_attr(response, "output")
    if not isinstance(output, dict):
        return b""

    audio = output.get("audio")
    if isinstance(audio, dict):
        data = audio.get("data") or audio.get("audio")
        if isinstance(data, str):
            try:
                return base64.b64decode(data)
            except Exception:
                logger.exception("DashScope TTS: failed to decode audio data")
                return b""
        if isinstance(data, bytes):
            return data

    for key in ("audio", "data"):
        data = output.get(key)
        if isinstance(data, bytes):
            return data
        if isinstance(data, str):
            try:
                return base64.b64decode(data)
            except Exception:
                logger.exception("DashScope TTS: failed to decode %s", key)
                return b""

    return b""


class DashScopeTTS(TTSBase):
    """DashScope Qwen TTS over HTTP streaming."""

    def __init__(self, config: Settings):
        self._config = config

        if config.dashscope_api_key:
            dashscope.api_key = config.dashscope_api_key

        if config.dashscope_region == "cn":
            dashscope.base_http_api_url = "https://dashscope.aliyuncs.com/api/v1"
        else:
            dashscope.base_http_api_url = "https://dashscope-intl.aliyuncs.com/api/v1"

        logger.info(
            "DashScopeTTS initialized for HTTP streaming (model=%s, region=%s)",
            config.tts_model,
            config.dashscope_region,
        )

    async def _run_blocking(self, function, *args):
        return await asyncio.to_thread(function, *args)

    def _call_tts(self, text: str, cfg: TTSConfig) -> Generator[Any, None, None] | Any:
        kwargs: dict[str, Any] = {
            "model": self._config.tts_model,
            "text": text,
            "voice": cfg.voice,
            "stream": True,
            "result_format": "pcm",
            "sample_rate": cfg.sample_rate,
        }
        language_type = _language_type(cfg.language)
        if language_type:
            kwargs["language_type"] = language_type

        return MultiModalConversation.call(**kwargs)

    async def _yield_tts_audio(self, text: str, cfg: TTSConfig) -> AsyncGenerator[bytes, None]:
        text = text.strip()
        if not text:
            return

        try:
            response_stream = await self._run_blocking(self._call_tts, text, cfg)
        except Exception as exc:
            logger.error("DashScope TTS request failed: %s", exc)
            return

        received_audio = False
        for response in response_stream:
            status_code = _response_attr(response, "status_code")
            if status_code not in (None, HTTPStatus.OK, 200):
                logger.error(
                    "DashScope TTS error: status=%s code=%s message=%s request_id=%s",
                    status_code,
                    _response_attr(response, "code"),
                    _response_attr(response, "message"),
                    _response_attr(response, "request_id"),
                )
                continue

            audio_bytes = _extract_audio_bytes(response)
            if audio_bytes:
                received_audio = True
                yield audio_bytes

        if not received_audio:
            logger.warning(
                "DashScope TTS finished without audio (model=%s, voice=%s, text_len=%s)",
                self._config.tts_model,
                cfg.voice,
                len(text),
            )

    @staticmethod
    def _should_flush_text(buffer: str) -> bool:
        stripped = buffer.strip()
        if len(stripped) >= _MAX_STREAM_TEXT_CHARS:
            return True
        return len(stripped) >= _MIN_STREAM_TEXT_CHARS and bool(_SENTENCE_END_RE.search(stripped))

    async def synthesize_stream(
        self,
        text_iterator: AsyncGenerator[str, None],
        config: TTSConfig | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """Convert streamed text into streamed audio chunks."""
        cfg = config or TTSConfig(
            voice=self._config.tts_voice,
            language=self._config.tts_language,
        )

        buffer = ""
        async for text_chunk in text_iterator:
            if not text_chunk.strip():
                continue
            buffer = f"{buffer}{text_chunk}"
            if not self._should_flush_text(buffer):
                continue
            text_to_speak = buffer.strip()
            buffer = ""
            async for audio_bytes in self._yield_tts_audio(text_to_speak, cfg):
                yield audio_bytes

        if buffer.strip():
            async for audio_bytes in self._yield_tts_audio(buffer, cfg):
                yield audio_bytes

    async def synthesize(
        self,
        text: str,
        config: TTSConfig | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """Synthesize complete text to streamed audio."""

        async def _text_gen():
            yield text

        async for chunk in self.synthesize_stream(_text_gen(), config):
            yield chunk

    async def close(self) -> None:
        """Clean up resources."""
        pass

"""
Generic OpenAI-compatible LLM provider.

Works with any OpenAI API-compatible service:
- OpenAI (api.openai.com)
- DashScope/Qwen (dashscope-intl.aliyuncs.com)
- 9router, Groq, Together, etc.
"""

import json
import logging
from typing import Any, AsyncGenerator, Optional

import httpx

from app.core.config import Settings
from app.core.exceptions import UpstreamServiceError
from app.infra.contracts import LLMBase, Message

logger = logging.getLogger(__name__)


def _extract_choice_content(choice: dict[str, Any]) -> str:
    """Extract content from common OpenAI-compatible streaming and non-streaming shapes."""
    delta = choice.get("delta")
    if isinstance(delta, dict):
        content = delta.get("content")
        if isinstance(content, str):
            return content

    message = choice.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, str):
            return content

    text = choice.get("text")
    if isinstance(text, str):
        return text

    return ""


def _extract_completion_content(data: dict[str, Any]) -> str:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return ""
    choice = choices[0]
    if not isinstance(choice, dict):
        return ""
    return _extract_choice_content(choice)


def _extract_finish_reason(data: dict[str, Any]) -> str | None:
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        return None
    choice = choices[0]
    if not isinstance(choice, dict):
        return None
    reason = choice.get("finish_reason")
    return reason if isinstance(reason, str) and reason else None


def _looks_incomplete_text(text: str) -> bool:
    stripped = text.rstrip()
    if not stripped:
        return False
    if stripped[-1] in ".!?。！？\"')]}":
        return False
    return True


def _should_continue_incomplete_output(text: str) -> bool:
    stripped = text.strip()
    if len(stripped) < 25:
        return False
    if stripped.startswith(("{", "[")):
        return False
    return _looks_incomplete_text(stripped)


class OpenAILLM(LLMBase):
    """Generic OpenAI-compatible LLM client using httpx to handle non-strict SSE streams."""

    def __init__(self, config: Settings):
        self._config = config
        self._model = config.llm_model
        
        self._client = httpx.AsyncClient(
            base_url=config.llm_base_url,
            headers={
                "Authorization": f"Bearer {config.llm_api_key}",
                "Content-Type": "application/json",
            },
            timeout=120.0,
        )
        logger.info(f"OpenAILLM initialized (model={self._model}, base_url={config.llm_base_url})")

    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion."""

        api_messages = []

        prompt = system_prompt or self._config.llm_system_prompt
        if prompt:
            api_messages.append({"role": "system", "content": prompt})

        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        logger.info(f"--- LLM INPUT ({self._model}) ---\n" + "\n".join([f"[{m['role'].upper()}]: {m['content']}" for m in api_messages]))

        payload = {
            "model": self._model,
            "messages": api_messages,
            "stream": True,
            "temperature": self._config.llm_temperature,
            "max_tokens": max_tokens or self._config.llm_max_tokens,
        }

        async def _stream_request(
            request_payload: dict[str, Any],
            *,
            phase: str,
            response_parts: list[str],
            stats: dict[str, Any],
        ) -> AsyncGenerator[str, None]:
            stats["raw_samples"] = []
            stats["raw_tail_samples"] = []
            stats["finish_reason"] = None
            stats["stream_line_count"] = 0
            stats["content_chunk_count"] = 0

            async with self._client.stream("POST", "/chat/completions", json=request_payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line == "data: [DONE]":
                        break
                    data_str = line[len("data: "):] if line.startswith("data: ") else line
                    stats["stream_line_count"] += 1
                    if len(stats["raw_samples"]) < 3:
                        stats["raw_samples"].append(data_str[:500])
                    stats["raw_tail_samples"].append(data_str[:500])
                    if len(stats["raw_tail_samples"]) > 3:
                        stats["raw_tail_samples"].pop(0)
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse LLM chunk (phase=%s): %s", phase, data_str)
                        continue

                    stats["finish_reason"] = _extract_finish_reason(data) or stats["finish_reason"]
                    content = _extract_completion_content(data)
                    if content:
                        stats["content_chunk_count"] += 1
                        response_parts.append(content)
                        yield content

        try:
            full_response: list[str] = []
            primary_stats: dict[str, Any] = {}
            async for content in _stream_request(
                payload,
                phase="primary",
                response_parts=full_response,
                stats=primary_stats,
            ):
                yield content

            output = "".join(full_response)
            logger.info(
                "LLM stream finished (model=%s, finish_reason=%s, max_tokens=%s, stream_lines=%s, content_chunks=%s, output_chars=%s)",
                self._model,
                primary_stats.get("finish_reason"),
                payload["max_tokens"],
                primary_stats.get("stream_line_count"),
                primary_stats.get("content_chunk_count"),
                len(output),
            )

            if _should_continue_incomplete_output(output):
                logger.warning(
                    "LLM output appears incomplete; requesting one continuation (model=%s, finish_reason=%s, output_chars=%s, raw_tail_samples=%s)",
                    self._model,
                    primary_stats.get("finish_reason"),
                    len(output),
                    primary_stats.get("raw_tail_samples"),
                )
                continuation_payload = {
                    **payload,
                    "messages": [
                        *api_messages,
                        {"role": "assistant", "content": output},
                        {
                            "role": "user",
                            "content": (
                                "Your previous message stopped mid-sentence. "
                                "Continue from exactly where it stopped and finish the same reply. "
                                "Return only the remaining words, no recap."
                            ),
                        },
                    ],
                    "max_tokens": min(240, int(payload["max_tokens"])),
                }
                continuation_stats: dict[str, Any] = {}
                async for content in _stream_request(
                    continuation_payload,
                    phase="continuation",
                    response_parts=full_response,
                    stats=continuation_stats,
                ):
                    yield content
                output = "".join(full_response)
                logger.info(
                    "LLM continuation finished (model=%s, finish_reason=%s, stream_lines=%s, content_chunks=%s, output_chars=%s)",
                    self._model,
                    continuation_stats.get("finish_reason"),
                    continuation_stats.get("stream_line_count"),
                    continuation_stats.get("content_chunk_count"),
                    len(output),
                )

            if output:
                logger.info(f"--- LLM OUTPUT ({self._model}) ---\n" + output)
                if primary_stats.get("finish_reason") == "length":
                    logger.warning(
                        "LLM output stopped because max_tokens was reached (model=%s, max_tokens=%s, output_chars=%s)",
                        self._model,
                        payload["max_tokens"],
                        len(output),
                    )
                elif _looks_incomplete_text(output):
                    logger.warning(
                        "LLM output appears incomplete despite finish_reason=%s (model=%s, output_chars=%s, raw_tail_samples=%s)",
                        primary_stats.get("finish_reason"),
                        self._model,
                        len(output),
                        primary_stats.get("raw_tail_samples"),
                    )
            else:
                logger.warning(
                    "LLM stream completed with empty output (model=%s, finish_reason=%s, raw_samples=%s, raw_tail_samples=%s)",
                    self._model,
                    primary_stats.get("finish_reason"),
                    primary_stats.get("raw_samples"),
                    primary_stats.get("raw_tail_samples"),
                )

        except httpx.HTTPStatusError as e:
            error_text = await e.response.aread()
            logger.error(f"HTTP Status Error: {e.response.status_code} - {error_text.decode('utf-8', errors='ignore')}")
            raise UpstreamServiceError(f"LLM API error ({e.response.status_code}).") from e
        except Exception as e:
            logger.error(f"OpenAI LLM connection error: {e}")
            raise UpstreamServiceError("LLM service is unavailable. Please try again.") from e

    async def close(self) -> None:
        """Close the async client."""
        await self._client.aclose()

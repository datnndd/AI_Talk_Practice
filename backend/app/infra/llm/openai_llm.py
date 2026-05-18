"""OpenAI Responses API LLM provider."""

import json
import logging
from typing import Any, AsyncGenerator, Optional

import httpx

from app.core.config import Settings
from app.core.exceptions import UpstreamServiceError
from app.infra.contracts import LLMBase, Message

logger = logging.getLogger(__name__)


def _responses_input(messages: list[Message]) -> list[dict[str, str]]:
    return [{"role": msg.role, "content": msg.content} for msg in messages]


def _extract_response_message_text(message: dict[str, Any]) -> str:
    content = message.get("content")
    if not isinstance(content, list):
        return ""

    parts: list[str] = []
    for item in content:
        if not isinstance(item, dict):
            continue
        text = item.get("text")
        if isinstance(text, str):
            parts.append(text)
    return "".join(parts)


def _extract_response_output_text(response_data: dict[str, Any]) -> str:
    output_text = response_data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    output = response_data.get("output")
    if not isinstance(output, list):
        return ""

    parts: list[str] = []
    for item in output:
        if isinstance(item, dict) and item.get("type") == "message":
            parts.append(_extract_response_message_text(item))
    return "".join(parts)


def _extract_response_delta(data: dict[str, Any]) -> str:
    event_type = data.get("type")
    if event_type in {"response.output_text.delta", "response.refusal.delta"}:
        delta = data.get("delta")
        return delta if isinstance(delta, str) else ""
    return ""


def _extract_response_status(data: dict[str, Any]) -> str | None:
    response = data.get("response")
    if isinstance(response, dict):
        status = response.get("status")
        if isinstance(status, str):
            return status

    status = data.get("status")
    return status if isinstance(status, str) else None


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
    """LLM client backed by OpenAI Responses API."""

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
        logger.info("OpenAILLM initialized for Responses API (model=%s, base_url=%s)", self._model, config.llm_base_url)

    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream text chunks from Responses API while preserving old LLMBase interface."""

        prompt = system_prompt or self._config.llm_system_prompt
        api_input = _responses_input(messages)
        logger.info(
            "--- LLM INPUT (%s) ---\n[INSTRUCTIONS]: %s\n%s",
            self._model,
            prompt or "",
            "\n".join([f"[{m['role'].upper()}]: {m['content']}" for m in api_input]),
        )

        payload: dict[str, Any] = {
            "model": self._model,
            "input": api_input,
            "stream": True,
            "temperature": self._config.llm_temperature,
            "max_output_tokens": max_tokens or self._config.llm_max_tokens,
        }
        if prompt:
            payload["instructions"] = prompt

        async def _stream_request(
            request_payload: dict[str, Any],
            *,
            phase: str,
            response_parts: list[str],
            stats: dict[str, Any],
        ) -> AsyncGenerator[str, None]:
            stats["raw_samples"] = []
            stats["raw_tail_samples"] = []
            stats["status"] = None
            stats["stream_line_count"] = 0
            stats["content_chunk_count"] = 0
            stats["completed_text"] = ""

            async with self._client.stream("POST", "/responses", json=request_payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line or line.startswith("event: "):
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
                    if not isinstance(data, dict):
                        logger.debug("Ignoring non-object LLM chunk (phase=%s): %s", phase, data_str[:300])
                        continue

                    stats["status"] = _extract_response_status(data) or stats["status"]
                    event_type = data.get("type")
                    if event_type == "response.completed":
                        response_data = data.get("response")
                        if isinstance(response_data, dict):
                            stats["completed_text"] = _extract_response_output_text(response_data)
                        continue
                    if event_type == "response.failed":
                        response_data = data.get("response")
                        error = response_data.get("error") if isinstance(response_data, dict) else None
                        raise UpstreamServiceError(f"LLM API response failed: {error or data_str[:300]}")

                    content = _extract_response_delta(data)
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
            if not output and primary_stats.get("completed_text"):
                output = str(primary_stats["completed_text"])
                full_response.append(output)
                yield output

            logger.info(
                "LLM stream finished (model=%s, status=%s, max_output_tokens=%s, stream_lines=%s, content_chunks=%s, output_chars=%s)",
                self._model,
                primary_stats.get("status"),
                payload["max_output_tokens"],
                primary_stats.get("stream_line_count"),
                primary_stats.get("content_chunk_count"),
                len(output),
            )

            if _should_continue_incomplete_output(output):
                logger.warning(
                    "LLM output appears incomplete; requesting one continuation (model=%s, status=%s, output_chars=%s, raw_tail_samples=%s)",
                    self._model,
                    primary_stats.get("status"),
                    len(output),
                    primary_stats.get("raw_tail_samples"),
                )
                continuation_payload = {
                    **payload,
                    "input": [
                        *api_input,
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
                    "max_output_tokens": min(240, int(payload["max_output_tokens"])),
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
                    "LLM continuation finished (model=%s, status=%s, stream_lines=%s, content_chunks=%s, output_chars=%s)",
                    self._model,
                    continuation_stats.get("status"),
                    continuation_stats.get("stream_line_count"),
                    continuation_stats.get("content_chunk_count"),
                    len(output),
                )

            if output:
                logger.info("--- LLM OUTPUT (%s) ---\n%s", self._model, output)
                if primary_stats.get("status") == "incomplete":
                    logger.warning(
                        "LLM output stopped because max_output_tokens was reached (model=%s, max_output_tokens=%s, output_chars=%s)",
                        self._model,
                        payload["max_output_tokens"],
                        len(output),
                    )
                elif _looks_incomplete_text(output):
                    logger.warning(
                        "LLM output appears incomplete despite status=%s (model=%s, output_chars=%s, raw_tail_samples=%s)",
                        primary_stats.get("status"),
                        self._model,
                        len(output),
                        primary_stats.get("raw_tail_samples"),
                    )
            else:
                logger.warning(
                    "LLM stream completed with empty output (model=%s, status=%s, raw_samples=%s, raw_tail_samples=%s)",
                    self._model,
                    primary_stats.get("status"),
                    primary_stats.get("raw_samples"),
                    primary_stats.get("raw_tail_samples"),
                )

        except httpx.HTTPStatusError as e:
            error_text = await e.response.aread()
            logger.error("HTTP Status Error: %s - %s", e.response.status_code, error_text.decode("utf-8", errors="ignore"))
            raise UpstreamServiceError(f"LLM API error ({e.response.status_code}).") from e
        except UpstreamServiceError:
            raise
        except Exception as e:
            logger.error("OpenAI LLM connection error: %s", e)
            raise UpstreamServiceError("LLM service is unavailable. Please try again.") from e

    async def close(self) -> None:
        """Close the async client."""
        await self._client.aclose()

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

        try:
            full_response = []
            raw_samples: list[str] = []
            
            async with self._client.stream("POST", "/chat/completions", json=payload) as response:
                response.raise_for_status()
                
                async for line in response.aiter_lines():
                    line = line.strip()
                    if not line:
                        continue
                    if line == "data: [DONE]":
                        break
                    data_str = line[len("data: "):] if line.startswith("data: ") else line
                    if len(raw_samples) < 3:
                        raw_samples.append(data_str[:500])
                    try:
                        data = json.loads(data_str)
                    except json.JSONDecodeError:
                        logger.warning(f"Failed to parse LLM chunk: {data_str}")
                        continue

                    content = _extract_completion_content(data)
                    if content:
                        full_response.append(content)
                        yield content

            output = "".join(full_response)
            if output:
                logger.info(f"--- LLM OUTPUT ({self._model}) ---\n" + output)
            else:
                logger.warning(
                    "LLM stream completed with empty output (model=%s, raw_samples=%s)",
                    self._model,
                    raw_samples,
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

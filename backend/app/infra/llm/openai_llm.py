"""
Generic OpenAI-compatible LLM provider.

Works with any OpenAI API-compatible service:
- OpenAI (api.openai.com)
- DashScope/Qwen (dashscope-intl.aliyuncs.com)
- Groq, Together, etc.
"""

import logging
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.core.config import Settings
from app.infra.contracts import LLMBase, Message

logger = logging.getLogger(__name__)


class OpenAILLM(LLMBase):
    """Generic OpenAI-compatible LLM client."""

    def __init__(self, config: Settings):
        self._config = config
        self._client = AsyncOpenAI(
            api_key=config.llm_api_key,
            base_url=config.llm_base_url,
        )
        self._model = config.llm_model
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

        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=api_messages,
                stream=True,
                temperature=self._config.llm_temperature,
                max_tokens=max_tokens or self._config.llm_max_tokens,
            )

            full_response = []
            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response.append(content)
                    yield content
            
            logger.info(f"--- LLM OUTPUT ({self._model}) ---\n" + "".join(full_response))

        except Exception as e:
            logger.error(f"OpenAI LLM error: {e}")
            yield f"Sorry, I encountered an error: {str(e)}"

    async def close(self) -> None:
        """Close the async client."""
        await self._client.close()

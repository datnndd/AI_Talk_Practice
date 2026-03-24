"""
Gemini LLM provider via OpenAI-compatible API.

Uses Google's Gemini models through the OpenAI-compatible endpoint,
allowing easy integration with the same client library.
"""

import logging
from typing import AsyncGenerator, Optional

from openai import AsyncOpenAI

from app.config import Settings
from app.services.base import LLMBase, Message

logger = logging.getLogger(__name__)


class GeminiLLM(LLMBase):
    """Gemini LLM via OpenAI-compatible endpoint."""

    def __init__(self, config: Settings):
        self._config = config
        self._client = AsyncOpenAI(
            api_key=config.gemini_api_key,
            base_url=config.llm_base_url,
        )
        self._model = config.llm_model
        logger.info(f"GeminiLLM initialized (model={self._model})")

    async def chat_stream(
        self,
        messages: list[Message],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """Stream chat completion from Gemini."""

        # Build message list
        api_messages = []

        # Add system prompt
        prompt = system_prompt or self._config.llm_system_prompt
        if prompt:
            api_messages.append({"role": "system", "content": prompt})

        # Add conversation history
        for msg in messages:
            api_messages.append({"role": msg.role, "content": msg.content})

        try:
            stream = await self._client.chat.completions.create(
                model=self._model,
                messages=api_messages,
                stream=True,
                temperature=0.7,
                max_tokens=512,
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"Gemini LLM error: {e}")
            yield f"Sorry, I encountered an error: {str(e)}"

    async def close(self) -> None:
        """Close the async client."""
        await self._client.close()

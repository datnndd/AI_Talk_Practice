import asyncio
import time

import pytest

import app.modules.sessions.services.conversation as conversation_module
from app.core.config import Settings
from app.infra.contracts import Message
from app.modules.sessions.services.conversation import ConversationSession


class DummyASR:
    async def start_session(self, language="en", sample_rate=16000):
        return None

    async def feed_audio(self, audio_chunk: bytes):
        return None

    async def get_transcript(self):
        return None

    async def stop_session(self):
        return None

    async def close(self):
        return None


class CapturingLLM:
    def __init__(self, _config):
        self.calls = []

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": [(message.role, message.content) for message in messages],
                "max_tokens": max_tokens,
            }
        )
        yield "Hello"
        yield " world"

    async def close(self):
        return None


class DelayedPullTTS:
    def __init__(self, _config):
        pass

    async def synthesize_stream(self, text_iterator, config=None):
        await asyncio.sleep(0.08)
        async for text_chunk in text_iterator:
            if text_chunk:
                yield f"audio::{text_chunk}".encode("utf-8")

    async def synthesize(self, text, config=None):
        yield f"audio::{text}".encode("utf-8")

    async def close(self):
        return None


class ImmediateTTS:
    def __init__(self, _config):
        pass

    async def synthesize_stream(self, text_iterator, config=None):
        async for text_chunk in text_iterator:
            if text_chunk:
                yield f"audio::{text_chunk}".encode("utf-8")

    async def synthesize(self, text, config=None):
        yield f"audio::{text}".encode("utf-8")

    async def close(self):
        return None


@pytest.mark.asyncio
async def test_llm_chunks_stream_before_tts_begins_pulling(monkeypatch):
    llm_instances = []

    def _create_llm(config):
        instance = CapturingLLM(config)
        llm_instances.append(instance)
        return instance

    monkeypatch.setattr(conversation_module, "create_asr", lambda config: DummyASR())
    monkeypatch.setattr(conversation_module, "create_llm", _create_llm)
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: DelayedPullTTS(config))

    llm_chunk_times = []
    audio_chunk_times = []

    async def on_llm_chunk(text, is_done):
        if text and not is_done:
            llm_chunk_times.append(time.perf_counter())

    async def on_audio_chunk(audio_bytes):
        if audio_bytes is not None:
            audio_chunk_times.append(time.perf_counter())

    session = ConversationSession(Settings())
    await session.initialize(
        on_transcript=lambda *_: asyncio.sleep(0),
        on_llm_chunk=on_llm_chunk,
        on_audio_chunk=on_audio_chunk,
        on_error=lambda *_: asyncio.sleep(0),
        system_prompt="Test prompt",
    )

    started_at = time.perf_counter()
    await session._run_response_pipeline("Test user turn")
    await session.close()

    assert llm_chunk_times, "Expected streamed LLM chunks"
    assert audio_chunk_times, "Expected streamed audio chunks"
    assert llm_chunk_times[0] - started_at < 0.05
    assert audio_chunk_times[0] - started_at >= 0.07


@pytest.mark.asyncio
async def test_conversation_history_is_trimmed_before_llm_call(monkeypatch):
    llm_instances = []

    def _create_llm(config):
        instance = CapturingLLM(config)
        llm_instances.append(instance)
        return instance

    settings = Settings(llm_history_message_limit=3)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: DummyASR())
    monkeypatch.setattr(conversation_module, "create_llm", _create_llm)
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: ImmediateTTS(config))

    session = ConversationSession(settings)
    await session.initialize(
        on_transcript=lambda *_: asyncio.sleep(0),
        on_llm_chunk=lambda *_: asyncio.sleep(0),
        on_audio_chunk=lambda *_: asyncio.sleep(0),
        on_error=lambda *_: asyncio.sleep(0),
        system_prompt="Trim prompt",
    )
    session._messages = [
        Message(role="user", content="u1"),
        Message(role="assistant", content="a1"),
        Message(role="user", content="u2"),
        Message(role="assistant", content="a2"),
    ]

    await session._run_response_pipeline("u3")
    await session.close()

    assert llm_instances[0].calls[0]["messages"] == [
        ("user", "u2"),
        ("assistant", "a2"),
        ("user", "u3"),
    ]

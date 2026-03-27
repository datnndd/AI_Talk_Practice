import base64
import json

import pytest
import pytest_asyncio
from fastapi import WebSocketDisconnect
from sqlalchemy import delete, select

import app.conversation as conversation_module
import app.main as main_module
from app.auth import create_access_token, hash_password
from app.models.message import Message
from app.models.scenario import Scenario
from app.models.session import Session
from app.models.user import User
from app.services.base import TranscriptEvent, TranscriptType
from conftest import TestingSessionLocal


class FakeWebSocket:
    def __init__(self, messages):
        self._messages = [json.dumps(message) for message in messages]
        self.sent = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def receive_text(self):
        if self._messages:
            return self._messages.pop(0)
        raise WebSocketDisconnect(code=1000)

    async def send_json(self, data):
        self.sent.append(data)

    async def close(self):
        self.closed = True


class StubASR:
    def __init__(self, _config):
        self.language = "en"
        self.audio_chunks = []

    async def start_session(self, language="en", sample_rate=16000):
        self.language = language

    async def feed_audio(self, audio_chunk: bytes):
        self.audio_chunks.append(audio_chunk)

    async def get_transcript(self):
        return None

    async def stop_session(self):
        if not self.audio_chunks:
            return None
        return TranscriptEvent(
            text="Hello from the user",
            type=TranscriptType.FINAL,
            language=self.language,
        )

    async def close(self):
        return None


class StubLLM:
    def __init__(self, _config):
        self.calls = []

    async def chat_stream(self, messages, system_prompt=None):
        self.calls.append({
            "system_prompt": system_prompt,
            "messages": [(message.role, message.content) for message in messages],
        })
        yield "Hello "
        yield "from the assistant"

    async def close(self):
        return None


class StubTTS:
    def __init__(self, _config):
        self.configs = []

    async def synthesize_stream(self, text_iterator, config=None):
        self.configs.append(config)
        async for text_chunk in text_iterator:
            yield f"audio::{text_chunk}".encode("utf-8")

    async def synthesize(self, text, config=None):
        self.configs.append(config)
        yield f"audio::{text}".encode("utf-8")

    async def close(self):
        return None


@pytest_asyncio.fixture
async def clean_realtime_tables():
    async with TestingSessionLocal() as session:
        await session.execute(delete(Message))
        await session.execute(delete(Session))
        await session.execute(delete(Scenario))
        await session.execute(delete(User))
        await session.commit()
    yield


@pytest_asyncio.fixture
async def test_user(clean_realtime_tables):
    async with TestingSessionLocal() as session:
        user = User(
            email="ws-test@example.com",
            password_hash=hash_password("password123"),
            display_name="Realtime Tester",
            native_language="vi",
            target_language="en",
            level="beginner",
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest_asyncio.fixture
async def test_scenario(clean_realtime_tables):
    async with TestingSessionLocal() as session:
        scenario = Scenario(
            title="Realtime Scenario",
            description="Scenario used for websocket tests",
            learning_objectives="Practice live conversation",
            ai_system_prompt="You are roleplaying a calm interviewer.",
            category="business",
            difficulty="medium",
            is_active=True,
        )
        session.add(scenario)
        await session.commit()
        await session.refresh(scenario)
        return scenario


@pytest.fixture
def realtime_stubs(monkeypatch):
    llm_instances = []

    def create_llm(config):
        instance = StubLLM(config)
        llm_instances.append(instance)
        return instance

    monkeypatch.setattr(main_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: StubASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", create_llm)
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

    return {"llm_instances": llm_instances}


@pytest.mark.asyncio
async def test_session_start_and_turn_persist_messages(test_user, test_scenario, realtime_stubs):
    token = create_access_token(test_user.id)
    audio_payload = base64.b64encode(b"\x01\x02" * 4000).decode("ascii")
    websocket = FakeWebSocket(
        [
            {
                "type": "session_start",
                "token": token,
                "scenario_id": test_scenario.id,
                "language": "en",
                "voice": "Cherry",
            },
            {"type": "start_recording", "language": "en", "voice": "Cherry"},
            {"type": "audio_chunk", "data": audio_payload},
            {"type": "stop_recording"},
        ]
    )

    await main_module.websocket_conversation(websocket)

    assert websocket.accepted is True
    assert websocket.sent[0]["type"] == "session_started"
    assert websocket.sent[0]["scenario_id"] == test_scenario.id
    assert websocket.sent[1]["type"] == "recording_started"
    assert any(message["type"] == "transcript_final" and message["text"] == "Hello from the user" for message in websocket.sent)
    assert any(message["type"] == "llm_done" and message["text"] == "Hello from the assistant" for message in websocket.sent)
    assert any(message["type"] == "audio_chunk" for message in websocket.sent)
    assert websocket.sent[-1]["type"] == "audio_done"

    async with TestingSessionLocal() as session:
        session_result = await session.execute(select(Session))
        sessions = session_result.scalars().all()
        message_result = await session.execute(select(Message).order_by(Message.order_index))
        messages = message_result.scalars().all()

    assert len(sessions) == 1
    assert sessions[0].user_id == test_user.id
    assert sessions[0].scenario_id == test_scenario.id
    assert sessions[0].status == "completed"
    assert sessions[0].duration_seconds is not None

    assert [(message.role, message.content, message.order_index) for message in messages] == [
        ("user", "Hello from the user", 1),
        ("assistant", "Hello from the assistant", 2),
    ]

    llm_call = realtime_stubs["llm_instances"][0].calls[0]
    assert llm_call["system_prompt"] == test_scenario.ai_system_prompt
    assert llm_call["messages"] == [("user", "Hello from the user")]


@pytest.mark.asyncio
async def test_session_start_rejects_invalid_token(test_scenario, realtime_stubs):
    websocket = FakeWebSocket(
        [
            {
                "type": "session_start",
                "token": "invalid-token",
                "scenario_id": test_scenario.id,
            },
        ]
    )

    await main_module.websocket_conversation(websocket)

    assert websocket.sent == [{"type": "error", "message": "Invalid token"}]
    assert websocket.closed is True

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Session))
        assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_session_start_rejects_missing_scenario(test_user, realtime_stubs):
    token = create_access_token(test_user.id)
    websocket = FakeWebSocket(
        [
            {
                "type": "session_start",
                "token": token,
                "scenario_id": 999999,
            },
        ]
    )

    await main_module.websocket_conversation(websocket)

    assert websocket.sent == [{"type": "error", "message": "Scenario not found"}]
    assert websocket.closed is True

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Session))
        assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_disconnect_without_user_turn_marks_session_abandoned(test_user, test_scenario, realtime_stubs):
    token = create_access_token(test_user.id)
    websocket = FakeWebSocket(
        [
            {
                "type": "session_start",
                "token": token,
                "scenario_id": test_scenario.id,
            },
        ]
    )

    await main_module.websocket_conversation(websocket)

    assert websocket.sent[0]["type"] == "session_started"

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Session))
        session = result.scalar_one()

    assert session.status == "abandoned"
    assert session.duration_seconds is None

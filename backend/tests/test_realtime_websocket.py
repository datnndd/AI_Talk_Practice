import asyncio
import base64
import json

import pytest
import pytest_asyncio
from fastapi import WebSocketDisconnect
from sqlalchemy import delete, select

import app.modules.sessions.services.conversation as conversation_module
import app.main as main_module
import app.modules.sessions.routers.ws as ws_module
from app.core.security import create_access_token, hash_password
from app.infra.contracts import TranscriptEvent, TranscriptType
from app.modules.sessions.models.message import Message
from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.models.session import Session
from app.modules.users.models.user import User
from conftest import TestingSessionLocal


class FakeWebSocket:
    def __init__(self, messages, message_delay=0):
        self._messages = [json.dumps(message) for message in messages]
        self._message_delay = message_delay
        self.sent = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def receive_text(self):
        if self._messages:
            if self._message_delay:
                await asyncio.sleep(self._message_delay)
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


class EmptyTranscriptASR(StubASR):
    async def stop_session(self):
        return TranscriptEvent(
            text="",
            type=TranscriptType.FINAL,
            language=self.language,
        )


class AutoFinalASR(StubASR):
    def __init__(self, _config):
        super().__init__(_config)
        self._final_emitted = False

    async def get_transcript(self):
        if self.audio_chunks and not self._final_emitted:
            self._final_emitted = True
            return TranscriptEvent(
                text="Hello from auto-final ASR",
                type=TranscriptType.FINAL,
                language=self.language,
            )
        return None

    async def stop_session(self):
        return None


class SpeechStoppedASR(StubASR):
    def __init__(self, _config):
        super().__init__(_config)
        self._speech_end_emitted = False

    async def get_transcript(self):
        if self.audio_chunks and not self._speech_end_emitted:
            self._speech_end_emitted = True
            return TranscriptEvent(
                text="",
                type=TranscriptType.SPEECH_END,
                language=self.language,
            )
        return None

    async def stop_session(self):
        return TranscriptEvent(
            text="Hello from speech-stopped ASR",
            type=TranscriptType.FINAL,
            language=self.language,
        )


class PartialThenFinalASR(StubASR):
    def __init__(self, _config):
        super().__init__(_config)
        self._partial_emitted = False

    async def get_transcript(self):
        if self.audio_chunks and not self._partial_emitted:
            self._partial_emitted = True
            return TranscriptEvent(
                text="This should stay hidden while recording",
                type=TranscriptType.PARTIAL,
                language=self.language,
            )
        return None


class GracefulSpeechStoppedASR(StubASR):
    def __init__(self, _config):
        super().__init__(_config)
        self._speech_end_emitted = False

    async def get_transcript(self):
        if self.audio_chunks and not self._speech_end_emitted:
            self._speech_end_emitted = True
            return TranscriptEvent(
                text="",
                type=TranscriptType.SPEECH_END,
                language=self.language,
            )
        return None

    async def stop_session(self):
        return TranscriptEvent(
            text=f"Captured {len(self.audio_chunks)} chunks",
            type=TranscriptType.FINAL,
            language=self.language,
        )


class LessonAnswerASR(StubASR):
    async def stop_session(self):
        if not self.audio_chunks:
            return None
        return TranscriptEvent(
            text="I can practice live conversation naturally today.",
            type=TranscriptType.FINAL,
            language=self.language,
        )


class StubLLM:
    def __init__(self, _config):
        self.calls = []

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append({
            "system_prompt": system_prompt,
            "messages": [(message.role, message.content) for message in messages],
            "max_tokens": max_tokens,
        })
        yield "Hello "
        await asyncio.sleep(0.05)
        yield "from the assistant"

    async def close(self):
        return None


class LessonPlanLLM:
    def __init__(self, _config):
        self.calls = []

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append({
            "system_prompt": system_prompt,
            "messages": [(message.role, message.content) for message in messages],
            "max_tokens": max_tokens,
        })
        yield json.dumps({
            "opening_message": "Welcome. Could you introduce yourself and the role you are practicing for?",
            "goals": [
                {
                    "goal": "Introduce background",
                    "question": "What background should I know about?",
                    "success_criteria": ["target role", "relevant experience"],
                    "follow_up_questions": ["Which experience is most relevant?"],
                    "vocabulary": ["target role", "relevant experience"],
                },
                {
                    "goal": "Explain one achievement",
                    "question": "Tell me about one achievement.",
                    "success_criteria": ["project", "result"],
                    "follow_up_questions": ["What was your result?"],
                    "vocabulary": ["project", "result"],
                },
            ],
        })

    async def close(self):
        return None


class BrokenLessonPlanLLM:
    def __init__(self, _config):
        self.calls = []

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append({
            "system_prompt": system_prompt,
            "messages": [(message.role, message.content) for message in messages],
            "max_tokens": max_tokens,
        })
        yield '{"opening_message":"Welcome","goals":[{"goal":"Order a drink","success_criteria":["drink"]'

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

    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
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

    await ws_module.websocket_conversation(websocket)

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
async def test_stop_recording_without_audio_emits_no_input_and_does_not_persist_message(
    test_user,
    test_scenario,
    realtime_stubs,
):
    token = create_access_token(test_user.id)
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
            {"type": "stop_recording"},
        ]
    )

    await ws_module.websocket_conversation(websocket)

    assert any(
        message["type"] == "asr_no_input" and message["reason"] == "no_audio"
        for message in websocket.sent
    )
    assert not any(message["type"] == "transcript_final" for message in websocket.sent)

    async with TestingSessionLocal() as session:
        message_result = await session.execute(select(Message))
        messages = message_result.scalars().all()

    assert messages == []


@pytest.mark.asyncio
async def test_empty_asr_transcript_emits_no_input_and_does_not_persist_message(
    test_user,
    test_scenario,
    monkeypatch,
):
    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: EmptyTranscriptASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", lambda config: StubLLM(config))
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

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

    await ws_module.websocket_conversation(websocket)

    assert any(
        message["type"] == "asr_no_input" and message["reason"] == "empty_transcript"
        for message in websocket.sent
    )
    assert not any(message["type"] == "llm_done" for message in websocket.sent)

    async with TestingSessionLocal() as session:
        message_result = await session.execute(select(Message))
        messages = message_result.scalars().all()

    assert messages == []


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

    await ws_module.websocket_conversation(websocket)

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

    await ws_module.websocket_conversation(websocket)

    assert websocket.sent == [{"type": "error", "message": "Scenario not found"}]


@pytest.mark.asyncio
async def test_session_start_with_active_session_id_resumes_without_creating_second_session(
    test_user,
    test_scenario,
    realtime_stubs,
    monkeypatch,
):
    monkeypatch.setattr(ws_module.settings, "ws_resume_grace_seconds", 30)
    token = create_access_token(test_user.id)
    first_socket = FakeWebSocket(
        [
            {
                "type": "session_start",
                "token": token,
                "scenario_id": test_scenario.id,
                "metadata": {"resume_enabled": True},
            },
        ]
    )

    await ws_module.websocket_conversation(first_socket)
    session_id = first_socket.sent[0]["session_id"]

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Session))
        sessions = result.scalars().all()
    assert len(sessions) == 1
    assert sessions[0].status == "active"

    second_socket = FakeWebSocket(
        [
            {
                "type": "session_start",
                "token": token,
                "scenario_id": test_scenario.id,
                "session_id": session_id,
                "metadata": {"resume_enabled": False},
            },
        ]
    )

    await ws_module.websocket_conversation(second_socket)

    assert second_socket.sent[0]["type"] == "session_started"
    assert second_socket.sent[0]["session_id"] == session_id

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Session))
        sessions = result.scalars().all()
    assert len(sessions) == 1
    assert sessions[0].id == session_id
    assert sessions[0].status == "abandoned"


@pytest.mark.asyncio
async def test_time_limit_emits_conversation_end_and_session_finalized(
    test_user,
    clean_realtime_tables,
    monkeypatch,
):
    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: StubASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", lambda config: StubLLM(config))
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

    async with TestingSessionLocal() as session:
        scenario = Scenario(
            title="Timeout Scenario",
            description="Scenario used for timeout tests",
            learning_objectives="Practice briefly",
            ai_system_prompt="You are a concise partner.",
            category="business",
            difficulty="medium",
            is_active=True,
            estimated_duration=1,
        )
        session.add(scenario)
        await session.commit()
        await session.refresh(scenario)
        scenario_id = scenario.id

    token = create_access_token(test_user.id)
    websocket = FakeWebSocket(
        [
            {
                "type": "session_start",
                "token": token,
                "scenario_id": scenario_id,
                "language": "en",
                "voice": "Cherry",
            },
            *[
                {"type": "config", "language": "en", "voice": "Cherry"}
                for _ in range(8)
            ],
        ],
        message_delay=0.2,
    )

    await ws_module.websocket_conversation(websocket)

    assert any(
        message["type"] == "conversation_end" and message["reason"] == "time_limit_reached"
        for message in websocket.sent
    )
    assert any(
        message["type"] == "session_finalized" and message["reason"] == "time_limit_reached"
        for message in websocket.sent
    )

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Session))
        finalized = result.scalar_one()

    assert finalized.status == "abandoned"
    assert finalized.session_metadata["end_reason"] == "time_limit_reached"


@pytest.mark.asyncio
async def test_final_asr_event_auto_triggers_llm_without_stop_recording(test_user, test_scenario, monkeypatch):
    llm_instances = []

    def create_llm(config):
        instance = StubLLM(config)
        llm_instances.append(instance)
        return instance

    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(ws_module.settings, "asr_finalization_grace_ms", 10)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: AutoFinalASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", create_llm)
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

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
            {"type": "config", "language": "en", "voice": "Cherry"},
        ],
        message_delay=0.05,
    )

    await ws_module.websocket_conversation(websocket)

    assert any(
        message["type"] == "transcript_final" and message["text"] == "Hello from auto-final ASR"
        for message in websocket.sent
    )
    assert any(
        message["type"] == "llm_done" and message["text"] == "Hello from the assistant"
        for message in websocket.sent
    )

    async with TestingSessionLocal() as session:
        message_result = await session.execute(select(Message).order_by(Message.order_index))
        messages = message_result.scalars().all()

    assert [(message.role, message.content, message.order_index) for message in messages] == [
        ("user", "Hello from auto-final ASR", 1),
        ("assistant", "Hello from the assistant", 2),
    ]
    assert llm_instances[0].calls[0]["messages"] == [("user", "Hello from auto-final ASR")]

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Session))
        sessions = result.scalars().all()

    assert len(sessions) == 1
    assert sessions[0].status == "completed"


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

    await ws_module.websocket_conversation(websocket)

    assert websocket.sent[0]["type"] == "session_started"

    async with TestingSessionLocal() as session:
        result = await session.execute(select(Session))
        session = result.scalar_one()

    assert session.status == "abandoned"
    assert session.duration_seconds is None


@pytest.mark.asyncio
async def test_speech_stopped_event_auto_finalizes_turn(test_user, test_scenario, monkeypatch):
    llm_instances = []

    def create_llm(config):
        instance = StubLLM(config)
        llm_instances.append(instance)
        return instance

    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(ws_module.settings, "asr_finalization_grace_ms", 10)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: SpeechStoppedASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", create_llm)
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

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
            {"type": "config", "language": "en", "voice": "Cherry"},
        ],
        message_delay=0.05,
    )

    await ws_module.websocket_conversation(websocket)

    assert any(
        message["type"] == "transcript_final" and message["text"] == "Hello from speech-stopped ASR"
        for message in websocket.sent
    )
    assert any(
        message["type"] == "llm_done" and message["text"] == "Hello from the assistant"
        for message in websocket.sent
    )

    async with TestingSessionLocal() as session:
        message_result = await session.execute(select(Message).order_by(Message.order_index))
        messages = message_result.scalars().all()

    assert [(message.role, message.content, message.order_index) for message in messages] == [
        ("user", "Hello from speech-stopped ASR", 1),
        ("assistant", "Hello from the assistant", 2),
    ]
    assert llm_instances[0].calls[0]["messages"] == [("user", "Hello from speech-stopped ASR")]


@pytest.mark.asyncio
async def test_partial_transcripts_are_sent_to_client_while_recording(test_user, test_scenario, monkeypatch):
    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: PartialThenFinalASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", lambda config: StubLLM(config))
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

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
        ],
        message_delay=0.05,
    )

    await ws_module.websocket_conversation(websocket)

    assert any(
        message["type"] == "transcript_partial" and message["text"] == "This should stay hidden while recording"
        for message in websocket.sent
    )
    assert any(
        message["type"] == "transcript_final" and message["text"] == "Hello from the user"
        for message in websocket.sent
    )


@pytest.mark.asyncio
async def test_speech_end_waits_for_trailing_audio_before_finalizing(test_user, test_scenario, monkeypatch):
    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(ws_module.settings, "asr_finalization_grace_ms", 90)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: GracefulSpeechStoppedASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", lambda config: StubLLM(config))
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

    token = create_access_token(test_user.id)
    first_audio = base64.b64encode(b"\x01\x02" * 4000).decode("ascii")
    trailing_audio = base64.b64encode(b"\x03\x04" * 4000).decode("ascii")
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
            {"type": "audio_chunk", "data": first_audio},
            {"type": "audio_chunk", "data": trailing_audio},
            {"type": "config", "language": "en", "voice": "Cherry"},
            {"type": "config", "language": "en", "voice": "Cherry"},
        ],
        message_delay=0.05,
    )

    await ws_module.websocket_conversation(websocket)

    assert any(
        message["type"] == "transcript_final" and message["text"] == "Captured 2 chunks"
        for message in websocket.sent
    )


@pytest.mark.asyncio
async def test_interrupt_assistant_stops_stream_and_persists_partial_reply(test_user, test_scenario, realtime_stubs):
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
            {"type": "interrupt_assistant"},
        ],
        message_delay=0.01,
    )

    await ws_module.websocket_conversation(websocket)

    assert any(message["type"] == "assistant_interrupted" for message in websocket.sent)
    assert not any(message["type"] == "llm_done" for message in websocket.sent)

    async with TestingSessionLocal() as session:
        message_result = await session.execute(select(Message).order_by(Message.order_index))
        messages = message_result.scalars().all()

    assert messages[0].role == "user"
    assert messages[0].content == "Hello from the user"
    assert len(messages) in {1, 2}
    if len(messages) == 2:
        assert messages[1].role == "assistant"
        assert messages[1].content == "Hello"


@pytest.mark.asyncio
async def test_lesson_engine_emits_state_and_structured_reply_events(test_user, test_scenario, monkeypatch):
    llm_instances = []
    planning_llm_instances = []

    def create_llm(config):
        instance = StubLLM(config)
        llm_instances.append(instance)
        return instance

    def create_planning_llm(config):
        instance = LessonPlanLLM(config)
        planning_llm_instances.append(instance)
        return instance

    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(ws_module, "create_llm", create_planning_llm)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: LessonAnswerASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", create_llm)
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

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
                "metadata": {"conversation_engine": "lesson_v1"},
            },
            {"type": "start_recording", "language": "en", "voice": "Cherry"},
            {"type": "audio_chunk", "data": audio_payload},
            {"type": "stop_recording"},
        ]
    )

    await ws_module.websocket_conversation(websocket)

    assert any(message["type"] == "lesson_started" for message in websocket.sent)
    assert any(message["type"] == "lesson_state" for message in websocket.sent)
    assert any(
        message["type"] == "llm_done" and "Which experience is most relevant?" in message["text"]
        for message in websocket.sent
    )

    async with TestingSessionLocal() as session:
        message_result = await session.execute(select(Message).order_by(Message.order_index))
        messages = message_result.scalars().all()

    assert [message.role for message in messages] == ["assistant", "user", "assistant"]
    assert "could you introduce yourself" in messages[0].content.lower()
    assert messages[1].content == "I can practice live conversation naturally today."
    assert messages[2].content == "Which experience is most relevant?"
    assert planning_llm_instances[0].calls
    assert planning_llm_instances[0].calls[0]["max_tokens"] == 2400
    assert llm_instances[0].calls == []


@pytest.mark.asyncio
async def test_lesson_engine_reports_generation_error_without_default_questions(test_user, test_scenario, monkeypatch):
    planning_llm_instances = []

    def create_planning_llm(config):
        instance = BrokenLessonPlanLLM(config)
        planning_llm_instances.append(instance)
        return instance

    monkeypatch.setattr(ws_module, "AsyncSessionLocal", TestingSessionLocal)
    monkeypatch.setattr(ws_module, "create_llm", create_planning_llm)
    monkeypatch.setattr(conversation_module, "create_asr", lambda config: LessonAnswerASR(config))
    monkeypatch.setattr(conversation_module, "create_llm", lambda config: StubLLM(config))
    monkeypatch.setattr(conversation_module, "create_tts", lambda config: StubTTS(config))

    token = create_access_token(test_user.id)
    websocket = FakeWebSocket(
        [
            {
                "type": "session_start",
                "token": token,
                "scenario_id": test_scenario.id,
                "language": "en",
                "voice": "Cherry",
                "metadata": {"conversation_engine": "lesson_v1"},
            },
        ]
    )

    await ws_module.websocket_conversation(websocket)

    assert any(
        message["type"] == "error"
        and message.get("code") == "lesson_plan_generation_failed"
        and "incomplete lesson plan" in message["message"].lower()
        for message in websocket.sent
    )
    assert not any(message["type"] == "lesson_started" for message in websocket.sent)
    assert not any(message["type"] == "llm_done" for message in websocket.sent)
    assert planning_llm_instances[0].calls[0]["max_tokens"] == 2400

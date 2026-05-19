from types import SimpleNamespace

import pytest

from app.modules.sessions.services.conversation_support import ConversationReplyService

class ChunkLLM:
    def __init__(self, chunks: list[str]):
        self.chunks = chunks
        self.calls = []

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append(
            {
                "messages": [(message.role, message.content) for message in messages],
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
            }
        )
        for chunk in self.chunks:
            yield chunk

def _session():
    return SimpleNamespace(
        scenario=SimpleNamespace(
            title="Coffee Shop Delay",
            description="Ask politely about a delayed coffee order.",
            user_role="Customer",
            ai_role="Barista",
            tasks=["Ask for an update", "Stay polite"],
        ),
        session_metadata={},
        messages=[
            SimpleNamespace(role="assistant", content="Hi, welcome to Highlands Coffee.", order_index=1),
            SimpleNamespace(role="user", content="I would like order a cup of coffee.", order_index=2),
        ],
    )

async def _collect_stream(chunks: list[str]):
    llm = ChunkLLM(chunks)
    stream = ConversationReplyService(llm=llm).stream_reply_with_end_decision(session=_session())
    text = ""
    async for chunk in stream:
        text += chunk
    return text, stream.should_end, llm

@pytest.mark.asyncio
async def test_end_marker_yes_is_stripped_and_sets_decision():
    text, should_end, _llm = await _collect_stream(["[[SESSION_END=yes]]\n", "Thank you. Have a nice day."])

    assert text == "Thank you. Have a nice day."
    assert should_end is True

@pytest.mark.asyncio
async def test_end_marker_no_is_stripped_and_keeps_session_open():
    text, should_end, _llm = await _collect_stream(["[[SESSION_END=no]]\n", "Could you tell me your order number?"])

    assert text == "Could you tell me your order number?"
    assert should_end is False

@pytest.mark.asyncio
async def test_missing_end_marker_keeps_content_and_defaults_no():
    text, should_end, _llm = await _collect_stream(["Could you tell me your order number?"])

    assert text == "Could you tell me your order number?"
    assert should_end is False

@pytest.mark.asyncio
async def test_split_end_marker_never_leaks_to_output():
    text, should_end, _llm = await _collect_stream(["[[SESSION", "_END=", "yes]]\nThanks", " again."])

    assert text == "Thanks again."
    assert should_end is True
    assert "SESSION_END" not in text

@pytest.mark.asyncio
async def test_reply_uses_recent_turns_prompt_not_history_messages():
    _text, _should_end, llm = await _collect_stream(["[[SESSION_END=no]]\nWhat size would you like?"])

    assert llm.calls[0]["messages"] == [
        ("user", "Continue the role-play after the learner says: I would like order a cup of coffee.")
    ]
    assert "Recent turns:" in llm.calls[0]["system_prompt"]
    assert "Assistant: Hi, welcome to Highlands Coffee." in llm.calls[0]["system_prompt"]
    assert "Learner: I would like order a cup of coffee." in llm.calls[0]["system_prompt"]

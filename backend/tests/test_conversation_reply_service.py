from types import SimpleNamespace

import pytest

from app.modules.sessions.services.conversation_support import ConversationReplyService

class ChunkLLM:
    def __init__(self, chunks: list[str]):
        self.chunks = chunks

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
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
        messages=[],
    )

async def _collect_stream(chunks: list[str]):
    stream = ConversationReplyService(llm=ChunkLLM(chunks)).stream_reply_with_end_decision(session=_session())
    text = ""
    async for chunk in stream:
        text += chunk
    return text, stream.should_end

@pytest.mark.asyncio
async def test_end_marker_yes_is_stripped_and_sets_decision():
    text, should_end = await _collect_stream(["[[SESSION_END=yes]]\n", "Thank you. Have a nice day."])

    assert text == "Thank you. Have a nice day."
    assert should_end is True

@pytest.mark.asyncio
async def test_end_marker_no_is_stripped_and_keeps_session_open():
    text, should_end = await _collect_stream(["[[SESSION_END=no]]\n", "Could you tell me your order number?"])

    assert text == "Could you tell me your order number?"
    assert should_end is False

@pytest.mark.asyncio
async def test_missing_end_marker_keeps_content_and_defaults_no():
    text, should_end = await _collect_stream(["Could you tell me your order number?"])

    assert text == "Could you tell me your order number?"
    assert should_end is False

@pytest.mark.asyncio
async def test_split_end_marker_never_leaks_to_output():
    text, should_end = await _collect_stream(["[[SESSION", "_END=", "yes]]\nThanks", " again."])

    assert text == "Thanks again."
    assert should_end is True
    assert "SESSION_END" not in text

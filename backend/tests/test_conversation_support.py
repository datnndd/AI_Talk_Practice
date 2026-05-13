import json

import pytest

from app.modules.sessions.services.conversation_support import RealtimeCorrectionService


class SequencedLLM:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append(
            {
                "messages": [(message.role, message.content) for message in messages],
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
            }
        )
        yield self.responses.pop(0)


@pytest.mark.asyncio
async def test_realtime_correction_retries_once_after_invalid_json():
    llm = SequencedLLM(
        [
            '{"is_good":false,"better_answer":"Hello. Good',
            json.dumps(
                {
                    "is_good": False,
                    "better_answer": "Hello. Good morning.",
                }
            ),
        ]
    )
    service = RealtimeCorrectionService(llm=llm, max_tokens=300)

    response = await service.correct(scenario_title="Greeting", text="Hello good morning")

    assert response.is_good is False
    assert response.better_answer == "Hello. Good morning."
    assert len(llm.calls) == 2
    assert "invalid or truncated JSON" in llm.calls[1]["system_prompt"]


@pytest.mark.asyncio
async def test_realtime_correction_falls_back_to_partial_corrected_text_when_json_stays_invalid():
    llm = SequencedLLM(
        [
            '{"better_answer":"Hello. Good morning.","is_good":',
            '{"better_answer":"Hello. Good morning.","is_good":',
        ]
    )
    service = RealtimeCorrectionService(llm=llm, max_tokens=300)

    response = await service.correct(scenario_title="Greeting", text="Hello good morning")

    assert response.is_good is True
    assert response.better_answer == "Hello. Good morning."
    assert response.persisted is False
    assert len(llm.calls) == 2

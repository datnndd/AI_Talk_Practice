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
            '{"corrected_text":"Hello. Good morning.","corrections":[{"original',
            json.dumps(
                {
                    "corrected_text": "Hello. Good morning.",
                    "corrections": [
                        {
                            "original_text": "Hello good morning",
                            "corrected_text": "Hello. Good morning.",
                            "explanation": "Add punctuation to separate the greeting naturally.",
                            "error_type": "naturalness",
                            "severity": "low",
                            "position_start": 0,
                            "position_end": 18,
                        }
                    ],
                }
            ),
        ]
    )
    service = RealtimeCorrectionService(llm=llm, max_tokens=300)

    response = await service.correct(scenario_title="Greeting", text="Hello good morning")

    assert response.corrected_text == "Hello. Good morning."
    assert len(response.corrections) == 1
    assert response.corrections[0].corrected_text == "Hello. Good morning."
    assert len(llm.calls) == 2
    assert "invalid or truncated JSON" in llm.calls[1]["system_prompt"]


@pytest.mark.asyncio
async def test_realtime_correction_falls_back_to_partial_corrected_text_when_json_stays_invalid():
    llm = SequencedLLM(
        [
            '{"corrected_text":"Hello. Good morning.","corrections":[{"original',
            '{"corrected_text":"Hello. Good morning.","corrections":[{"original',
        ]
    )
    service = RealtimeCorrectionService(llm=llm, max_tokens=300)

    response = await service.correct(scenario_title="Greeting", text="Hello good morning")

    assert response.corrected_text == "Hello. Good morning."
    assert response.corrections == []
    assert response.persisted is False
    assert len(llm.calls) == 2

import json

import pytest

from app.modules.sessions.services import session as session_service_module


class RouteHintLLM:
    def __init__(self, response):
        self.response = response
        self.closed = False

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        yield self.response

    async def close(self):
        self.closed = True


@pytest.mark.asyncio
async def test_session_hint_endpoint_uses_current_conversation_question(
    test_client,
    test_session,
    monkeypatch,
):
    llm = RouteHintLLM(
        json.dumps(
            {
                "analysis_vi": "AI dang hoi ban muon bat dau phan dat mon.",
                "answer_strategy_vi": "Hay tra loi bang mot yeu cau ngan gon va lich su.",
                "keywords": ["order", "please", "coffee"],
                "sample_answers": ["I would like a coffee, please.", "Can I order a latte, please?"],
                "sample_answer": "I would like a coffee, please.",
                "sample_answer_easy": "Coffee, please.",
            }
        )
    )
    monkeypatch.setattr(session_service_module, "create_llm_for_role", lambda settings, role: llm)

    response = await test_client.post(
        f"/api/sessions/{test_session.id}/hint",
        json={},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["lesson_id"] == f"hybrid-{test_session.scenario_id}"
    assert payload["question"] == "Please go ahead and order food."
    assert payload["analysis_vi"] == "AI dang hoi ban muon bat dau phan dat mon."
    assert payload["sample_answers"] == ["I would like a coffee, please.", "Can I order a latte, please?"]
    assert payload["sample_answer_easy"] == "Coffee, please."
    assert payload["metadata"]["source"] == "conversation_hint_prompt"
    assert llm.closed is True


@pytest.mark.asyncio
async def test_session_hint_endpoint_rejects_non_user_message(
    test_client,
    db_session,
    test_session,
):
    from app.modules.sessions.repository import SessionRepository

    message = await SessionRepository.add_message(
        db_session,
        session_id=test_session.id,
        role="assistant",
        content="What would you like to order?",
    )
    await db_session.commit()

    response = await test_client.post(
        f"/api/sessions/{test_session.id}/hint",
        json={"message_id": message.id},
    )

    assert response.status_code == 400

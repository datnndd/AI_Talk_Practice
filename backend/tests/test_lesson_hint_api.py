import json

import pytest

from app.modules.sessions.routers import lessons as lessons_router
from app.modules.sessions.services.lesson_runtime import LessonRuntimeService


class RouteHintLLM:
    def __init__(self, response):
        self.response = response
        self.closed = False
        self._config = type("Config", (), {"lesson_hint_llm_max_tokens": 700})()

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        yield self.response

    async def close(self):
        self.closed = True


async def _attach_lesson_metadata(db_session, test_session, test_scenario, test_user, *, question):
    package = LessonRuntimeService.create_lesson_package(scenario=test_scenario, level=test_user.level)
    state = LessonRuntimeService.initial_state(package)
    state.last_question = question
    test_session.session_metadata = {
        "lesson": LessonRuntimeService.serialize_lesson_metadata(
            package=package,
            state=state,
            hints={},
        )
    }
    db_session.add(test_session)
    await db_session.commit()
    return package


@pytest.mark.asyncio
async def test_lesson_hint_endpoint_uses_current_question_without_user_last_answer(
    test_client,
    db_session,
    test_session,
    test_scenario,
    test_user,
    monkeypatch,
):
    package = await _attach_lesson_metadata(
        db_session,
        test_session,
        test_scenario,
        test_user,
        question="Would you like that hot or iced?",
    )
    llm = RouteHintLLM(json.dumps({
        "question_analysis_vi": "AI dang hoi ban muon lua chon nong hay lanh.",
        "answer_strategy_vi": "Hay chon mot lua chon va noi them mot chi tiet ngan.",
        "keywords": ["hot", "iced", "please"],
        "sample_answers": ["I would like it iced, please.", "Hot is fine, thank you."],
        "simple_answer": "Iced, please.",
    }))
    monkeypatch.setattr(lessons_router, "create_llm", lambda settings: llm)

    response = await test_client.post(
        "/api/lessons/hint",
        json={
            "session_id": test_session.id,
            "lesson_id": package.lesson_id,
            "objective_id": package.objectives[0].objective_id,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["question"] == "Would you like that hot or iced?"
    assert payload["analysis_vi"] == "AI dang hoi ban muon lua chon nong hay lanh."
    assert payload["sample_answers"] == ["I would like it iced, please.", "Hot is fine, thank you."]
    assert payload["sample_answer_easy"] == "Iced, please."
    assert llm.closed is True


@pytest.mark.asyncio
async def test_lesson_hint_endpoint_rejects_mismatched_lesson_id(
    test_client,
    db_session,
    test_session,
    test_scenario,
    test_user,
):
    await _attach_lesson_metadata(
        db_session,
        test_session,
        test_scenario,
        test_user,
        question="What would you like to order today?",
    )

    response = await test_client.post(
        "/api/lessons/hint",
        json={
            "session_id": test_session.id,
            "lesson_id": "wrong-lesson-id",
        },
    )

    assert response.status_code == 400

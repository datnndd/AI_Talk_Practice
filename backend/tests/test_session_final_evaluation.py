import json

import pytest

from app.modules.sessions.models.session_score import SessionScore
from app.modules.sessions.schemas.session import MessageCreate
from app.modules.sessions.services.final_evaluation import SessionFinalEvaluationService
from app.modules.sessions.services.session import SessionService


class EvaluationLLM:
    def __init__(self, responses):
        self.calls = []
        self.responses = list(responses)

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": [(message.role, message.content) for message in messages],
                "max_tokens": max_tokens,
            }
        )
        payload = self.responses.pop(0)
        yield payload


@pytest.mark.asyncio
async def test_final_evaluation_creates_session_score(db_session, test_user, test_session):
    await SessionService.add_message(
        db_session,
        session_id=test_session.id,
        user_id=test_user.id,
        payload=MessageCreate(role="user", content="I need help writing this document."),
    )
    await SessionService.add_message(
        db_session,
        session_id=test_session.id,
        user_id=test_user.id,
        payload=MessageCreate(role="assistant", content="What kind of document is it?"),
    )

    evaluation_payload = {
        "pronunciation_score": 7.0,
        "fluency_score": 7.5,
        "grammar_score": 8.0,
        "vocabulary_score": 7.0,
        "intonation_score": 6.5,
        "relevance_score": 9.0,
        "overall_score": 7.8,
        "objective_completion": "completed",
        "strengths": ["Clear request"],
        "improvements": ["Add one deadline detail"],
        "corrections": [{"original": "help writing", "suggestion": "help me write"}],
        "next_steps": ["Practice giving context in one sentence"],
        "feedback_summary": "Bạn nói rõ mục tiêu chính và nên thêm thời hạn cụ thể hơn.",
    }
    personal_info_payload = {
        "personal_info": {"goal": "writing support"},
        "preferences": {"favorite_topics": ["documents"]},
        "notes": ["Learner often asks about writing tasks."],
    }
    llm = EvaluationLLM([json.dumps(evaluation_payload), json.dumps(personal_info_payload)])
    service = SessionFinalEvaluationService(llm=llm, max_tokens=900)

    score = await service.evaluate_and_store(db_session, session_id=test_session.id)
    await db_session.commit()

    assert isinstance(score, SessionScore)
    assert score.scored_message_count == 1
    assert score.overall_score == 7.8
    assert score.relevance_score == 9.0
    assert score.feedback_summary == evaluation_payload["feedback_summary"]
    assert score.score_metadata["source"] == "final_evaluation_llm"
    assert score.score_metadata["objective_completion"] == "completed"
    assert score.score_metadata["strengths"] == ["Clear request"]
    assert len(llm.calls) == 2
    assert "Airport Check-in" in llm.calls[0]["system_prompt"]
    assert test_user.preferences["conversation_profile"]["personal_info"]["goal"] == "writing support"


@pytest.mark.asyncio
async def test_final_evaluation_does_not_depend_on_message_scores(db_session, test_user, test_session):
    await SessionService.add_message(
        db_session,
        session_id=test_session.id,
        user_id=test_user.id,
        payload=MessageCreate(role="user", content="I need help writing this document."),
    )

    llm = EvaluationLLM(
        [
            json.dumps(
                {
                    "pronunciation_score": 6.0,
                    "fluency_score": 6.5,
                    "grammar_score": 7.0,
                    "vocabulary_score": 7.5,
                    "intonation_score": 6.0,
                    "relevance_score": 8.5,
                    "overall_score": 7.0,
                    "objective_completion": "partial",
                    "strengths": [],
                    "improvements": [],
                    "corrections": [],
                    "next_steps": [],
                    "feedback_summary": "Bạn bám đúng chủ đề.",
                }
            ),
            json.dumps({"personal_info": {}, "preferences": {}, "notes": []}),
        ]
    )
    service = SessionFinalEvaluationService(llm=llm, max_tokens=900)

    score = await service.evaluate_and_store(db_session, session_id=test_session.id)

    assert score.avg_pronunciation == 6.0
    assert score.relevance_score == 8.5
    assert "Message score evidence" not in llm.calls[0]["system_prompt"]


@pytest.mark.asyncio
async def test_final_evaluation_keeps_score_when_profile_extraction_fails(db_session, test_user, test_session):
    await SessionService.add_message(
        db_session,
        session_id=test_session.id,
        user_id=test_user.id,
        payload=MessageCreate(role="user", content="My goal is to check in at a hotel."),
    )

    llm = EvaluationLLM(
        [
            json.dumps(
                {
                    "pronunciation_score": 7.0,
                    "fluency_score": 7.0,
                    "grammar_score": 7.0,
                    "vocabulary_score": 7.0,
                    "intonation_score": 7.0,
                    "relevance_score": 8.0,
                    "overall_score": 7.2,
                    "objective_completion": "partial",
                    "strengths": ["Relevant answer"],
                    "improvements": ["Ask one follow-up question"],
                    "corrections": [],
                    "next_steps": ["Practice confirming reservation details"],
                    "feedback_summary": "Bạn trả lời đúng bối cảnh và nên hỏi thêm về đặt phòng.",
                }
            ),
            "not json",
            "still not json",
        ]
    )
    service = SessionFinalEvaluationService(llm=llm, max_tokens=900)

    score = await service.evaluate_and_store(db_session, session_id=test_session.id)

    assert isinstance(score, SessionScore)
    assert score.overall_score == 7.2
    assert score.feedback_summary == "Bạn trả lời đúng bối cảnh và nên hỏi thêm về đặt phòng."
    assert test_session.session_metadata["final_evaluation"]["evaluation_status"] == "completed"
    assert test_session.session_metadata["final_evaluation"]["profile_extraction_status"] == "failed"


@pytest.mark.asyncio
async def test_final_evaluation_failure_does_not_raise(db_session, test_user, test_session):
    await SessionService.add_message(
        db_session,
        session_id=test_session.id,
        user_id=test_user.id,
        payload=MessageCreate(role="user", content="I need help writing this document."),
    )
    llm = EvaluationLLM(["not json"])
    service = SessionFinalEvaluationService(llm=llm, max_tokens=900)

    score = await service.evaluate_and_store(db_session, session_id=test_session.id)

    assert score is None
    assert test_session.session_metadata["final_evaluation"]["evaluation_status"] == "failed"

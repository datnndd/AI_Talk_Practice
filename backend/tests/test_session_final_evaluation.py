import json

import pytest

from app.modules.sessions.models.session_score import SessionScore
from app.modules.sessions.repository import SessionRepository
from app.modules.sessions.schemas.session import MessageCreate
from app.modules.sessions.services.session import SessionService
from app.modules.sessions.services.hybrid_conversation.final_evaluation import SessionFinalEvaluationService


class EvaluationLLM:
    def __init__(self, chunks):
        self.calls = []
        self.chunks = chunks

    async def chat_stream(self, messages, system_prompt=None, max_tokens=None):
        self.calls.append(
            {
                "system_prompt": system_prompt,
                "messages": [(message.role, message.content) for message in messages],
                "max_tokens": max_tokens,
            }
        )
        for chunk in self.chunks:
            yield chunk


@pytest.mark.asyncio
async def test_final_evaluation_creates_session_score_without_message_scores(db_session, test_user, test_session):
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

    payload = {
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
    llm = EvaluationLLM([json.dumps(payload)])
    service = SessionFinalEvaluationService(llm=llm, max_tokens=900)

    score = await service.evaluate_and_store(db_session, session_id=test_session.id)
    await db_session.commit()

    assert isinstance(score, SessionScore)
    assert score.scored_message_count == 1
    assert score.overall_score == 7.8
    assert score.relevance_score == 9.0
    assert score.feedback_summary == payload["feedback_summary"]
    assert score.score_metadata["source"] == "final_evaluation_llm"
    assert score.score_metadata["objective_completion"] == "completed"
    assert score.score_metadata["strengths"] == ["Clear request"]
    assert llm.calls
    assert "FULL TRANSCRIPT" not in llm.calls[0]["system_prompt"]
    assert "Airport Check-in" in llm.calls[0]["system_prompt"]


@pytest.mark.asyncio
async def test_final_evaluation_uses_aggregate_as_evidence_when_available(db_session, test_user, test_session):
    await SessionService.add_message(
        db_session,
        session_id=test_session.id,
        user_id=test_user.id,
        payload=MessageCreate(
            role="user",
            content="I need help writing this document.",
            score={
                "pronunciation_score": 6.0,
                "fluency_score": 6.5,
                "grammar_score": 7.0,
                "vocabulary_score": 7.5,
                "intonation_score": 6.0,
                "overall_score": 6.8,
            },
        ),
    )
    aggregate = await SessionRepository.aggregate_message_scores(db_session, test_session.id)
    assert aggregate is not None

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
            )
        ]
    )
    service = SessionFinalEvaluationService(llm=llm, max_tokens=900)

    score = await service.evaluate_and_store(db_session, session_id=test_session.id)

    assert score.avg_pronunciation == 6.0
    assert score.relevance_score == 8.5
    assert "Message score evidence" in llm.calls[0]["system_prompt"]


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

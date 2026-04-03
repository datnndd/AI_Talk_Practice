import pytest
from app.models.message import Message
from app.repositories.session_repository import SessionRepository

@pytest.mark.asyncio
async def test_create_session(db_session, test_user, test_scenario):
    session = await SessionRepository.create_session(
        db_session,
        user_id=test_user.id,
        scenario_id=test_scenario.id,
        status="active"
    )
    assert session.id is not None
    assert session.user_id == test_user.id
    assert session.status == "active"

@pytest.mark.asyncio
async def test_add_message_with_scoring(db_session, test_session):
    message = await SessionRepository.add_message(
        db_session,
        session_id=test_session.id,
        role="user",
        content="Hello, I'd like to check in.",
        score={
            "pronunciation_score": 8.5,
            "fluency_score": 7.0,
            "grammar_score": 9.0,
            "vocabulary_score": 8.0,
            "intonation_score": 7.5,
            "overall_score": 8.0,
            "feedback": "Good job!",
            "metadata": {"engine": "test-grader"}
        },
        corrections=[
            {
                "original_text": "check in",
                "corrected_text": "check-in",
                "explanation": "Use a hyphen.",
                "error_type": "grammar",
                "severity": "low"
            }
        ]
    )
    assert message.id is not None
    assert message.role == "user"
    assert message.score is not None
    assert message.score.overall_score == 8.0
    assert len(message.corrections) == 1
    assert message.corrections[0].corrected_text == "check-in"

@pytest.mark.asyncio
async def test_aggregate_scores(db_session, test_session):
    # Add two scored messages
    await SessionRepository.add_message(
        db_session,
        session_id=test_session.id,
        role="user",
        content="Message 1",
        score={
            "pronunciation_score": 8, "fluency_score": 8, "grammar_score": 8, 
            "vocabulary_score": 8, "intonation_score": 8, "overall_score": 8
        }
    )
    await SessionRepository.add_message(
        db_session,
        session_id=test_session.id,
        role="user",
        content="Message 2",
        score={
            "pronunciation_score": 10, "fluency_score": 10, "grammar_score": 10, 
            "vocabulary_score": 10, "intonation_score": 10, "overall_score": 10
        }
    )
    
    aggregate = await SessionRepository.aggregate_message_scores(db_session, test_session.id)
    assert aggregate is not None
    assert aggregate["scored_message_count"] == 2
    assert aggregate["overall_score"] == 9.0
    assert aggregate["avg_pronunciation"] == 9.0

@pytest.mark.asyncio
async def test_upsert_session_score(db_session, test_session):
    values = {
        "overall_score": 8.5,
        "avg_pronunciation": 8.0,
        "avg_fluency": 7.0,
        "avg_grammar": 9.0,
        "avg_vocabulary": 8.0,
        "avg_intonation": 7.5,
        "relevance_score": 8.0,
        "scored_message_count": 5
    }
    score = await SessionRepository.upsert_session_score(db_session, session_id=test_session.id, values=values)
    assert score.session_id == test_session.id
    assert score.overall_score == 8.5
    
    # Update
    values["overall_score"] = 9.0
    score = await SessionRepository.upsert_session_score(db_session, session_id=test_session.id, values=values)
    assert score.overall_score == 9.0

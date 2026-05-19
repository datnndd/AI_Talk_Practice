import pytest
from app.modules.sessions.repository import SessionRepository

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
async def test_add_message_with_realtime_feedback(db_session, test_session):
    message = await SessionRepository.add_message(
        db_session,
        session_id=test_session.id,
        role="user",
        content="Hello, I'd like to check in.",
    )
    feedback = await SessionRepository.upsert_message_realtime_feedback(
        db_session,
        message_id=message.id,
        is_good=False,
        better_answer="Hello, I'd like to check in, please.",
        raw_response={"is_good": False, "better_answer": "Hello, I'd like to check in, please."},
    )

    assert message.id is not None
    assert message.role == "user"
    assert feedback.message_id == message.id
    assert feedback.is_good is False
    assert feedback.better_answer == "Hello, I'd like to check in, please."

@pytest.mark.asyncio
async def test_add_messages_without_per_message_scores(db_session, test_session):
    await SessionRepository.add_message(
        db_session,
        session_id=test_session.id,
        role="user",
        content="Message 1",
    )
    message = await SessionRepository.add_message(
        db_session,
        session_id=test_session.id,
        role="user",
        content="Message 2",
    )
    assert message.id is not None
    assert await SessionRepository.count_messages(db_session, test_session.id, role="user") == 2

@pytest.mark.asyncio
async def test_upsert_session_score(db_session, test_session):
    values = {
        "overall_score": 8.5,
        "avg_fluency": 7.0,
        "avg_grammar": 9.0,
        "avg_vocabulary": 8.0,
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

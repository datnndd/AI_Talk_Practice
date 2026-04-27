import pytest

from app.core.security import create_access_token
from app.modules.curriculum.models import LearningLevel, Lesson, LessonExercise


async def seed_curriculum(db_session):
    level = LearningLevel(code="A1", title="Beginner", order_index=0)
    db_session.add(level)
    await db_session.flush()
    lesson_1 = Lesson(level_id=level.id, title="First lesson", order_index=0, estimated_minutes=5)
    lesson_2 = Lesson(level_id=level.id, title="Second lesson", order_index=1, estimated_minutes=5)
    db_session.add_all([lesson_1, lesson_2])
    await db_session.flush()
    exercise_1 = LessonExercise(
        lesson_id=lesson_1.id,
        type="cloze_dictation",
        title="Fill the word",
        order_index=0,
        content={
            "passage": "I want a ___.",
            "blanks": [{"answer": "coffee", "accepted_answers": ["coffee"], "explanation_vi": "Do uong."}],
        },
        pass_score=100,
    )
    exercise_2 = LessonExercise(
        lesson_id=lesson_2.id,
        type="sentence_pronunciation",
        title="Say a sentence",
        order_index=0,
        content={"reference_text": "Hello there"},
        pass_score=80,
    )
    db_session.add_all([exercise_1, exercise_2])
    await db_session.commit()
    return level, lesson_1, lesson_2, exercise_1, exercise_2


@pytest.mark.asyncio
async def test_curriculum_locks_next_lesson_until_previous_completed(client, db_session, test_user):
    _, lesson_1, lesson_2, exercise_1, _ = await seed_curriculum(db_session)
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    response = await client.get("/api/curriculum", headers=headers)
    assert response.status_code == 200
    data = response.json()
    lessons = data["levels"][0]["lessons"]
    assert lessons[0]["id"] == lesson_1.id
    assert lessons[0]["is_locked"] is False
    assert lessons[1]["id"] == lesson_2.id
    assert lessons[1]["is_locked"] is True

    locked_response = await client.get(f"/api/lessons/{lesson_2.id}", headers=headers)
    assert locked_response.status_code == 403

    attempt = await client.post(
        f"/api/exercises/{exercise_1.id}/attempt",
        json={"answer": {"blanks": ["coffee"]}},
        headers=headers,
    )
    assert attempt.status_code == 201
    attempt_data = attempt.json()
    assert attempt_data["passed"] is True
    assert attempt_data["lesson_completed"] is True

    response = await client.get("/api/curriculum", headers=headers)
    lessons = response.json()["levels"][0]["lessons"]
    assert lessons[0]["progress_status"] == "completed"
    assert lessons[1]["is_locked"] is False


@pytest.mark.asyncio
async def test_vocab_pronunciation_requires_all_words(client, db_session, test_user):
    level = LearningLevel(code="VOCAB", title="Vocabulary", order_index=0)
    db_session.add(level)
    await db_session.flush()
    lesson = Lesson(level_id=level.id, title="Words", order_index=0)
    db_session.add(lesson)
    await db_session.flush()
    exercise = LessonExercise(
        lesson_id=lesson.id,
        type="vocab_pronunciation",
        title="Say words",
        order_index=0,
        content={"words": [{"word": "hello"}, {"word": "thanks"}]},
        pass_score=80,
    )
    db_session.add(exercise)
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    first = await client.post(
        f"/api/exercises/{exercise.id}/attempt",
        json={"answer": {"word": "hello", "transcript": "hello"}},
        headers=headers,
    )
    assert first.status_code == 201
    first_data = first.json()
    assert first_data["passed"] is False
    assert first_data["progress"]["state"]["passed_words"] == ["hello"]
    assert first_data["progress"]["state"]["retry_words"] == ["thanks"]

    second = await client.post(
        f"/api/exercises/{exercise.id}/attempt",
        json={"answer": {"word": "thanks", "transcript": "thanks"}},
        headers=headers,
    )
    assert second.status_code == 201
    second_data = second.json()
    assert second_data["passed"] is True
    assert sorted(second_data["progress"]["state"]["passed_words"]) == ["hello", "thanks"]


@pytest.mark.asyncio
async def test_admin_can_create_curriculum_with_exercise(admin_client):
    level_response = await admin_client.post(
        "/api/admin/curriculum/levels",
        json={"code": "B1", "title": "Intermediate", "order_index": 1},
    )
    assert level_response.status_code == 201
    level_id = level_response.json()["id"]

    lesson_response = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={"level_id": level_id, "title": "Travel listening", "order_index": 0, "estimated_minutes": 8},
    )
    assert lesson_response.status_code == 201
    lesson_id = lesson_response.json()["id"]

    exercise_response = await admin_client.post(
        "/api/admin/curriculum/exercises",
        json={
            "lesson_id": lesson_id,
            "type": "cloze_dictation",
            "title": "Missing words",
            "order_index": 0,
            "pass_score": 80,
            "content": {
                "passage": "I need a ___.",
                "blanks": [{"answer": "ticket", "accepted_answers": ["ticket"]}],
            },
        },
    )
    assert exercise_response.status_code == 201
    assert exercise_response.json()["type"] == "cloze_dictation"

    list_response = await admin_client.get("/api/admin/curriculum/levels")
    assert list_response.status_code == 200
    assert list_response.json()[0]["lessons"][0]["exercises"][0]["title"] == "Missing words"

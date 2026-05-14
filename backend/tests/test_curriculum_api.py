import base64

import pytest

from app.core.security import create_access_token
from app.modules.curriculum.models import LearningSection, Lesson, LessonAudioAsset, Unit


async def seed_curriculum(db_session):
    section = LearningSection(code="A1", title="A1 Starter", cefr_level="A1")
    db_session.add(section)
    await db_session.flush()
    unit_1 = Unit(section_id=section.id, title="First unit", estimated_minutes=5, is_active=True)
    unit_2 = Unit(section_id=section.id, title="Second unit", estimated_minutes=5, is_active=True)
    db_session.add_all([unit_1, unit_2])
    await db_session.flush()
    lesson_1 = Lesson(
        unit_id=unit_1.id,
        type="definition_choice",
        title="Choose the word",
        order_index=0,
        content={
            "definition_audio_url": "/static/uploads/lesson-audio/coffee.wav",
            "definition_text": "A hot drink.",
            "options": [
                {"word": "coffee", "is_correct": True},
                {"word": "tea", "is_correct": False},
                {"word": "milk", "is_correct": False},
                {"word": "water", "is_correct": False},
            ],
        },
        pass_score=100,
    )
    lesson_2 = Lesson(
        unit_id=unit_2.id,
        type="read_aloud",
        title="Read a sentence",
        order_index=0,
        content={"text": "Hello there"},
        pass_score=80,
    )
    db_session.add_all([lesson_1, lesson_2])
    await db_session.commit()
    return section, unit_1, unit_2, lesson_1, lesson_2


async def seed_cefr_curriculum(db_session):
    seeded = {}
    for index, cefr in enumerate(["A1", "A2", "B1", "B2"]):
        section = LearningSection(code=f"{cefr}_PATH", title=f"{cefr} Path", cefr_level=cefr)
        db_session.add(section)
        await db_session.flush()
        unit = Unit(section_id=section.id, title=f"{cefr} Unit", estimated_minutes=5, is_active=True)
        db_session.add(unit)
        await db_session.flush()
        lesson = Lesson(
            unit_id=unit.id,
            type="definition_choice",
            title=f"{cefr} Lesson",
            order_index=0,
            content={
                "definition_text": "A hot drink.",
                "options": [
                    {"word": "coffee", "is_correct": True},
                    {"word": "tea", "is_correct": False},
                    {"word": "milk", "is_correct": False},
                    {"word": "water", "is_correct": False},
                ],
            },
            pass_score=100,
        )
        db_session.add(lesson)
        seeded[cefr] = {"section": section, "unit": unit, "lesson": lesson}
    await db_session.commit()
    return seeded


@pytest.mark.asyncio
async def test_curriculum_locks_next_unit_until_previous_completed(client, db_session, test_user):
    section, unit_1, unit_2, lesson_1, _ = await seed_curriculum(db_session)
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    response = await client.get("/api/curriculum", headers=headers)
    assert response.status_code == 200
    data = response.json()
    units = next(item for item in data["sections"] if item["id"] == section.id)["units"]
    assert units[0]["id"] == unit_1.id
    assert units[0]["is_locked"] is False
    assert units[0]["lessons"] == []
    assert units[1]["id"] == unit_2.id
    assert units[1]["is_locked"] is True

    locked_response = await client.get(f"/api/units/{unit_2.id}", headers=headers)
    assert locked_response.status_code == 403

    unit_response = await client.get(f"/api/units/{unit_1.id}", headers=headers)
    assert unit_response.status_code == 200, unit_response.text
    unit_data = unit_response.json()
    assert unit_data["lessons"][0]["id"] == lesson_1.id
    assert "is_required" not in unit_data["lessons"][0]
    assert unit_data["lessons"][0]["content"]["definition_text"] == "A hot drink."

    attempt = await client.post(
        f"/api/lessons/{lesson_1.id}/attempt",
        json={"answer": {"selected_word": "coffee"}},
        headers=headers,
    )
    assert attempt.status_code == 201
    attempt_data = attempt.json()
    assert attempt_data["passed"] is True
    assert attempt_data["unit_completed"] is True

    response = await client.get("/api/curriculum", headers=headers)
    units = next(item for item in response.json()["sections"] if item["id"] == section.id)["units"]
    assert units[0]["progress_status"] == "completed"
    assert units[1]["is_locked"] is False


@pytest.mark.asyncio
async def test_curriculum_starts_at_user_current_cefr(client, db_session, test_user):
    seeded = await seed_cefr_curriculum(db_session)
    test_user.current_cefr = "B1"
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    response = await client.get("/api/curriculum", headers=headers)

    assert response.status_code == 200
    data = response.json()
    units_by_cefr = {section["cefr_level"]: section["units"][0] for section in data["sections"] if section["cefr_level"] in seeded}
    assert data["current_cefr"] == "B1"
    assert data["current_unit_id"] == seeded["B1"]["unit"].id
    assert units_by_cefr["A1"]["is_locked"] is False
    assert units_by_cefr["A2"]["is_locked"] is False
    assert units_by_cefr["B1"]["is_locked"] is False
    assert units_by_cefr["B2"]["is_locked"] is True

    locked_response = await client.get(f"/api/units/{seeded['B2']['unit'].id}", headers=headers)
    assert locked_response.status_code == 403


@pytest.mark.asyncio
async def test_curriculum_falls_back_to_a1_without_user_cefr(client, db_session, test_user):
    seeded = await seed_cefr_curriculum(db_session)
    test_user.current_cefr = None
    test_user.level = None
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    response = await client.get("/api/curriculum", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["current_cefr"] == "A1"
    assert data["current_unit_id"] == seeded["A1"]["unit"].id


@pytest.mark.asyncio
async def test_curriculum_uses_user_level_when_current_cefr_missing(client, db_session, test_user):
    seeded = await seed_cefr_curriculum(db_session)
    test_user.current_cefr = None
    test_user.level = "B1"
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    response = await client.get("/api/curriculum", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["current_cefr"] == "B1"
    assert data["current_unit_id"] == seeded["B1"]["unit"].id


@pytest.mark.asyncio
async def test_pronunciation_attempt_rejects_non_wav_audio(client, db_session, test_user, monkeypatch):
    from app.modules.curriculum import services as curriculum_services

    monkeypatch.setattr(curriculum_services.settings, "azure_speech_key", "test-key")
    monkeypatch.setattr(curriculum_services.settings, "azure_speech_region", "southeastasia")

    section = LearningSection(code="AUDIO_FORMAT", title="Audio format")
    db_session.add(section)
    await db_session.flush()
    unit = Unit(section_id=section.id, title="Pronunciation", is_active=True)
    db_session.add(unit)
    await db_session.flush()
    lesson = Lesson(
        unit_id=unit.id,
        type="shadowing",
        title="Say hello",
        order_index=0,
        content={"reference_text": "Hello", "sample_audio_url": "/static/uploads/lesson-audio/hello.wav"},
        pass_score=80,
    )
    db_session.add(lesson)
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}
    audio_base64 = f"data:audio/webm;base64,{base64.b64encode(b'not a wav').decode('ascii')}"

    response = await client.post(
        f"/api/lessons/{lesson.id}/attempt",
        json={"audio_base64": audio_base64},
        headers=headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Audio must be a valid WAV file"


@pytest.mark.asyncio
async def test_definition_choice_scores_selected_word(client, db_session, test_user):
    section = LearningSection(code="AUDIO", title="Audio")
    db_session.add(section)
    await db_session.flush()
    unit = Unit(section_id=section.id, title="Audio words", is_active=True)
    db_session.add(unit)
    await db_session.flush()
    lesson = Lesson(
        unit_id=unit.id,
        type="definition_choice",
        title="Choose word",
        order_index=0,
        content={
            "definition_audio_url": "/static/uploads/lesson-audio/reservation.wav",
            "definition_text": "A booking made before you arrive.",
            "options": [
                {"word": "reservation", "is_correct": True},
                {"word": "reception", "is_correct": False},
                {"word": "recommendation", "is_correct": False},
                {"word": "restaurant", "is_correct": False},
            ],
        },
        pass_score=100,
    )
    db_session.add(lesson)
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    wrong = await client.post(
        f"/api/lessons/{lesson.id}/attempt",
        json={"answer": {"selected_word": "reception"}},
        headers=headers,
    )
    assert wrong.status_code == 201
    assert wrong.json()["score"] == 0
    assert wrong.json()["passed"] is False

    correct = await client.post(
        f"/api/lessons/{lesson.id}/attempt",
        json={"answer": {"selected_word": "reservation"}},
        headers=headers,
    )
    assert correct.status_code == 201
    assert correct.json()["score"] == 100
    assert correct.json()["passed"] is True


@pytest.mark.asyncio
async def test_admin_can_create_curriculum_with_definition_choice_lesson(admin_client):
    section_response = await admin_client.post(
        "/api/admin/curriculum/sections",
        json={"code": "B1", "title": "B1 Independent", "cefr_level": "B1"},
    )
    assert section_response.status_code == 201
    section_id = section_response.json()["id"]

    unit_response = await admin_client.post(
        "/api/admin/curriculum/units",
        json={"section_id": section_id, "title": "Travel listening", "estimated_minutes": 8},
    )
    assert unit_response.status_code == 201
    unit_id = unit_response.json()["id"]

    lesson_response = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={
            "unit_id": unit_id,
            "type": "definition_choice",
            "title": "Pick reservation",
            "order_index": 0,
            "pass_score": 100,
            "content": {
                "definition_audio_url": "/static/uploads/lesson-audio/reservation.wav",
                "definition_text": "A booking made before you arrive.",
                "options": [
                    {"word": "reservation", "is_correct": True},
                    {"word": "reception", "is_correct": False},
                    {"word": "recommendation", "is_correct": False},
                    {"word": "restaurant", "is_correct": False},
                ],
            },
        },
    )
    assert lesson_response.status_code == 201
    assert lesson_response.json()["type"] == "definition_choice"
    assert "is_required" not in lesson_response.json()
    assert "audio_url" not in lesson_response.json()["content"]["options"][0]

    detail_response = await admin_client.get(f"/api/admin/curriculum/sections/{section_id}")
    assert detail_response.status_code == 200
    assert detail_response.json()["units"][0]["lessons"][0]["title"] == "Pick reservation"


@pytest.mark.asyncio
async def test_definition_choice_requires_one_correct_option(admin_client):
    section_response = await admin_client.post(
        "/api/admin/curriculum/sections",
        json={"code": "BAD", "title": "Bad"},
    )
    unit_response = await admin_client.post(
        "/api/admin/curriculum/units",
        json={"section_id": section_response.json()["id"], "title": "Bad unit"},
    )
    response = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={
            "unit_id": unit_response.json()["id"],
            "type": "definition_choice",
            "title": "Bad choice",
            "content": {
                "definition_audio_url": "/static/uploads/lesson-audio/reservation.wav",
                "options": [
                    {"word": "reservation", "is_correct": True},
                    {"word": "reception", "is_correct": True},
                    {"word": "recommendation", "is_correct": False},
                    {"word": "restaurant", "is_correct": False},
                ],
            },
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_create_lesson_defaults_sequential_title(admin_client):
    section_response = await admin_client.post(
        "/api/admin/curriculum/sections",
        json={"code": "SEQ", "title": "Sequential"},
    )
    unit_response = await admin_client.post(
        "/api/admin/curriculum/units",
        json={"section_id": section_response.json()["id"], "title": "Sequential unit"},
    )
    unit_id = unit_response.json()["id"]

    first = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={
            "unit_id": unit_id,
            "type": "read_aloud",
            "content": {"text": "Hello"},
        },
    )
    second = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={
            "unit_id": unit_id,
            "type": "read_aloud",
            "title": "",
            "content": {"text": "Good morning"},
        },
    )

    assert first.status_code == 201
    assert first.json()["title"] == "Lesson 1"
    assert second.status_code == 201
    assert second.json()["title"] == "Lesson 2"


@pytest.mark.asyncio
async def test_admin_reorder_swaps_without_unique_constraint_error(admin_client, db_session):
    section = LearningSection(code="REORDER", title="Reorder")
    db_session.add(section)
    await db_session.flush()
    unit_1 = Unit(section_id=section.id, title="First", is_active=True)
    unit_2 = Unit(section_id=section.id, title="Second", is_active=True)
    db_session.add_all([unit_1, unit_2])
    await db_session.flush()
    lesson_1 = Lesson(
        unit_id=unit_1.id,
        type="read_aloud",
        title="One",
        order_index=0,
        content={"text": "One"},
    )
    lesson_2 = Lesson(
        unit_id=unit_1.id,
        type="read_aloud",
        title="Two",
        order_index=1,
        content={"text": "Two"},
    )
    db_session.add_all([lesson_1, lesson_2])
    await db_session.commit()

    lesson_response = await admin_client.post(
        "/api/admin/curriculum/lessons/reorder",
        json={"items": [{"id": lesson_2.id, "order_index": 0}, {"id": lesson_1.id, "order_index": 1}]},
    )
    assert lesson_response.status_code == 204

    await db_session.refresh(lesson_1)
    await db_session.refresh(lesson_2)
    assert lesson_1.order_index == 1
    assert lesson_2.order_index == 0

@pytest.mark.asyncio
async def test_admin_tts_audio_creates_static_asset(admin_client, db_session, monkeypatch, tmp_path):
    from app.modules.curriculum import services as curriculum_services

    class StubTTS:
        async def synthesize(self, text, config=None):
            yield b"RIFF"
            yield text.encode("utf-8")

        async def close(self):
            pass

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(curriculum_services, "create_tts", lambda settings: StubTTS())

    response = await admin_client.post(
        "/api/admin/curriculum/audio/tts",
        json={"text": "hello", "voice": "Cherry", "language": "en"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["source"] == "tts"
    assert data["url"].startswith("/static/uploads/lesson-audio/")
    assert (tmp_path / data["url"].lstrip("/")).exists()
    asset = await db_session.get(LessonAudioAsset, data["id"])
    assert asset is not None
    assert asset.text == "hello"
    assert asset.size_bytes == len(b"RIFFhello")


@pytest.mark.asyncio
async def test_admin_audio_upload_accepts_audio_and_rejects_non_audio(admin_client, db_session, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    rejected = await admin_client.post(
        "/api/admin/curriculum/audio/upload",
        files={"file": ("note.txt", b"hello", "text/plain")},
    )
    assert rejected.status_code == 400

    accepted = await admin_client.post(
        "/api/admin/curriculum/audio/upload",
        files={"file": ("sample.wav", b"WAVE", "audio/wav")},
        data={"text": "sample", "language": "en"},
    )

    assert accepted.status_code == 201
    data = accepted.json()
    assert data["source"] == "upload"
    assert data["content_type"] == "audio/wav"
    assert data["url"].endswith(".wav")
    assert (tmp_path / data["url"].lstrip("/")).exists()
    asset = await db_session.get(LessonAudioAsset, data["id"])
    assert asset is not None
    assert asset.source == "upload"


@pytest.mark.asyncio
async def test_definition_choice_serializer_keeps_saved_options(client, db_session, test_user):
    section = LearningSection(code="NO_DICT", title="No dict")
    db_session.add(section)
    await db_session.flush()
    unit = Unit(section_id=section.id, title="Audio", is_active=True)
    db_session.add(unit)
    await db_session.flush()
    lesson = Lesson(
        unit_id=unit.id,
        type="definition_choice",
        title="Choose word",
        order_index=0,
        content={
            "definition_audio_url": "/static/uploads/lesson-audio/def.wav",
            "definition_text": "A booking.",
            "options": [
                {"word": "reservation", "meaning_vi": "\u0111\u1eb7t ch\u1ed7", "is_correct": True},
                {"word": "reception", "is_correct": False},
                {"word": "recommendation", "is_correct": False},
                {"word": "restaurant", "is_correct": False},
            ],
        },
        pass_score=100,
    )
    db_session.add(lesson)
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    response = await client.get(f"/api/units/{unit.id}", headers=headers)

    assert response.status_code == 200
    options = response.json()["lessons"][0]["content"]["options"]
    assert options[0]["meaning_vi"] == "\u0111\u1eb7t ch\u1ed7"
    assert "source" not in options[0]



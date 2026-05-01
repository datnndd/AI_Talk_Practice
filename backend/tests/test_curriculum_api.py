import base64

import pytest

from app.core.security import create_access_token
from app.modules.curriculum.models import DictionaryAudioCache, LearningSection, Lesson, Unit


async def seed_curriculum(db_session):
    section = LearningSection(code="A1", title="Beginner", cefr_level="A1", order_index=0)
    db_session.add(section)
    await db_session.flush()
    unit_1 = Unit(section_id=section.id, title="First unit", order_index=0, estimated_minutes=5)
    unit_2 = Unit(section_id=section.id, title="Second unit", order_index=1, estimated_minutes=5)
    db_session.add_all([unit_1, unit_2])
    await db_session.flush()
    lesson_1 = Lesson(
        unit_id=unit_1.id,
        type="cloze_dictation",
        title="Fill the word",
        order_index=0,
        content={
            "passage": "I want a ___.",
            "blanks": [{"answer": "coffee", "accepted_answers": ["coffee"], "explanation_vi": "Do uong."}],
        },
        pass_score=100,
    )
    lesson_2 = Lesson(
        unit_id=unit_2.id,
        type="sentence_pronunciation",
        title="Say a sentence",
        order_index=0,
        content={"reference_text": "Hello there"},
        pass_score=80,
    )
    db_session.add_all([lesson_1, lesson_2])
    await db_session.commit()
    return section, unit_1, unit_2, lesson_1, lesson_2


@pytest.mark.asyncio
async def test_curriculum_locks_next_unit_until_previous_completed(client, db_session, test_user):
    _, unit_1, unit_2, lesson_1, _ = await seed_curriculum(db_session)
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    response = await client.get("/api/curriculum", headers=headers)
    assert response.status_code == 200
    data = response.json()
    units = data["sections"][0]["units"]
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
    assert unit_data["lessons"][0]["content"]["passage"] == "I want a ___."

    attempt = await client.post(
        f"/api/lessons/{lesson_1.id}/attempt",
        json={"answer": {"blanks": ["coffee"]}},
        headers=headers,
    )
    assert attempt.status_code == 201
    attempt_data = attempt.json()
    assert attempt_data["passed"] is True
    assert attempt_data["unit_completed"] is True

    response = await client.get("/api/curriculum", headers=headers)
    units = response.json()["sections"][0]["units"]
    assert units[0]["progress_status"] == "completed"
    assert units[1]["is_locked"] is False


@pytest.mark.asyncio
async def test_vocab_pronunciation_requires_all_words(client, db_session, test_user):
    section = LearningSection(code="VOCAB", title="Vocabulary", order_index=0)
    db_session.add(section)
    await db_session.flush()
    unit = Unit(section_id=section.id, title="Words", order_index=0)
    db_session.add(unit)
    await db_session.flush()
    lesson = Lesson(
        unit_id=unit.id,
        type="vocab_pronunciation",
        title="Say words",
        order_index=0,
        content={"words": [{"word": "hello"}, {"word": "thanks"}]},
        pass_score=80,
    )
    db_session.add(lesson)
    await db_session.commit()
    headers = {"Authorization": f"Bearer {create_access_token(test_user.id)}"}

    first = await client.post(
        f"/api/lessons/{lesson.id}/attempt",
        json={"answer": {"word": "hello", "transcript": "hello"}},
        headers=headers,
    )
    assert first.status_code == 201
    first_data = first.json()
    assert first_data["passed"] is False
    assert first_data["progress"]["state"]["passed_words"] == ["hello"]
    assert first_data["progress"]["state"]["retry_words"] == ["thanks"]

    second = await client.post(
        f"/api/lessons/{lesson.id}/attempt",
        json={"answer": {"word": "thanks", "transcript": "thanks"}},
        headers=headers,
    )
    assert second.status_code == 201
    second_data = second.json()
    assert second_data["passed"] is True
    assert sorted(second_data["progress"]["state"]["passed_words"]) == ["hello", "thanks"]


@pytest.mark.asyncio
async def test_pronunciation_attempt_rejects_non_wav_audio(client, db_session, test_user, monkeypatch):
    from app.modules.curriculum import services as curriculum_services

    monkeypatch.setattr(curriculum_services.settings, "azure_speech_key", "test-key")
    monkeypatch.setattr(curriculum_services.settings, "azure_speech_region", "southeastasia")

    section = LearningSection(code="AUDIO_FORMAT", title="Audio format", order_index=0)
    db_session.add(section)
    await db_session.flush()
    unit = Unit(section_id=section.id, title="Pronunciation", order_index=0)
    db_session.add(unit)
    await db_session.flush()
    lesson = Lesson(
        unit_id=unit.id,
        type="sentence_pronunciation",
        title="Say hello",
        order_index=0,
        content={"reference_text": "Hello"},
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
async def test_word_audio_choice_scores_selected_word(client, db_session, test_user):
    section = LearningSection(code="AUDIO", title="Audio", order_index=0)
    db_session.add(section)
    await db_session.flush()
    unit = Unit(section_id=section.id, title="Audio words", order_index=0)
    db_session.add(unit)
    await db_session.flush()
    lesson = Lesson(
        unit_id=unit.id,
        type="word_audio_choice",
        title="Choose audio",
        order_index=0,
        content={
            "prompt_word": "reservation",
            "language": "en",
            "options": [
                {"word": "reservation", "is_correct": True},
                {"word": "reception", "is_correct": False},
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
async def test_admin_can_create_curriculum_with_word_audio_lesson(admin_client):
    section_response = await admin_client.post(
        "/api/admin/curriculum/sections",
        json={"code": "B1", "title": "Intermediate", "cefr_level": "B1", "order_index": 1},
    )
    assert section_response.status_code == 201
    section_id = section_response.json()["id"]

    unit_response = await admin_client.post(
        "/api/admin/curriculum/units",
        json={"section_id": section_id, "title": "Travel listening", "order_index": 0, "estimated_minutes": 8},
    )
    assert unit_response.status_code == 201
    unit_id = unit_response.json()["id"]

    lesson_response = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={
            "unit_id": unit_id,
            "type": "word_audio_choice",
            "title": "Pick reservation",
            "order_index": 0,
            "pass_score": 100,
            "content": {
                "prompt_word": "reservation",
                "language": "en",
                "options": [
                    {"word": "reservation", "is_correct": True},
                    {"word": "reception", "is_correct": False},
                ],
            },
        },
    )
    assert lesson_response.status_code == 201
    assert lesson_response.json()["type"] == "word_audio_choice"
    assert lesson_response.json()["content"]["options"][0]["audio_url"].startswith("/api/curriculum/dictionary/audio")

    list_response = await admin_client.get("/api/admin/curriculum/sections")
    assert list_response.status_code == 200
    assert list_response.json()[0]["units"][0]["lessons"][0]["title"] == "Pick reservation"


@pytest.mark.asyncio
async def test_word_audio_choice_requires_one_correct_option(admin_client):
    section_response = await admin_client.post(
        "/api/admin/curriculum/sections",
        json={"code": "BAD", "title": "Bad", "order_index": 0},
    )
    unit_response = await admin_client.post(
        "/api/admin/curriculum/units",
        json={"section_id": section_response.json()["id"], "title": "Bad unit", "order_index": 0},
    )
    response = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={
            "unit_id": unit_response.json()["id"],
            "type": "word_audio_choice",
            "title": "Bad choice",
            "content": {
                "prompt_word": "reservation",
                "options": [
                    {"word": "reservation", "is_correct": True},
                    {"word": "reception", "is_correct": True},
                ],
            },
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_create_lesson_defaults_sequential_title(admin_client):
    section_response = await admin_client.post(
        "/api/admin/curriculum/sections",
        json={"code": "SEQ", "title": "Sequential", "order_index": 0},
    )
    unit_response = await admin_client.post(
        "/api/admin/curriculum/units",
        json={"section_id": section_response.json()["id"], "title": "Sequential unit", "order_index": 0},
    )
    unit_id = unit_response.json()["id"]

    first = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={
            "unit_id": unit_id,
            "type": "sentence_pronunciation",
            "content": {"reference_text": "Hello"},
        },
    )
    second = await admin_client.post(
        "/api/admin/curriculum/lessons",
        json={
            "unit_id": unit_id,
            "type": "sentence_pronunciation",
            "title": "",
            "content": {"reference_text": "Good morning"},
        },
    )

    assert first.status_code == 201
    assert first.json()["title"] == "Lesson 1"
    assert second.status_code == 201
    assert second.json()["title"] == "Lesson 2"


@pytest.mark.asyncio
async def test_dictionary_audio_proxy_returns_cached_audio(client, db_session, monkeypatch):
    from app.modules.curriculum import services as curriculum_services

    class FakeResponse:
        content = b"audio"
        headers = {"content-type": "audio/mpeg"}
        url = "https://dict.minhqnd.com/api/v1/tts?word=hello&lang=en"

        def raise_for_status(self):
            return None

    class FakeClient:
        calls = 0

        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, *args, **kwargs):
            FakeClient.calls += 1
            return FakeResponse()

    monkeypatch.setattr(curriculum_services.httpx, "AsyncClient", FakeClient)

    first = await client.get("/api/curriculum/dictionary/audio?word=hello&lang=en")
    assert first.status_code == 200
    assert first.content == b"audio"
    assert first.headers["x-dictionary-source"] == "dict.minhqnd.com"

    second = await client.get("/api/curriculum/dictionary/audio?word=hello&lang=en")
    assert second.status_code == 200
    assert second.content == b"audio"
    assert FakeClient.calls == 1

    cached = (
        await db_session.execute(
            DictionaryAudioCache.__table__.select().where(DictionaryAudioCache.normalized_word == "hello")
        )
    ).first()
    assert cached is not None


@pytest.mark.asyncio
async def test_admin_dictionary_lookup_returns_meaning_and_audio_url(admin_client, monkeypatch):
    from app.modules.curriculum import services as curriculum_services

    class FakeResponse:
        def raise_for_status(self):
            return None

        def json(self):
            return {
                "exists": True,
                "word": "reservation",
                "results": [
                    {
                        "lang_code": "en",
                        "audio": "/api/v1/tts?word=reservation&lang=en",
                        "meanings": [
                            {
                                "definition": "sự đặt trước",
                                "definition_lang": "vi",
                            }
                        ],
                        "pronunciations": [{"ipa": "/rezərˈveɪʃən/"}],
                        "translations": [],
                    }
                ],
            }

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return None

        async def get(self, url, params):
            assert url.endswith("/api/v1/lookup")
            assert params == {"word": "reservation", "lang": "en", "def_lang": "vi"}
            return FakeResponse()

    monkeypatch.setattr(curriculum_services.httpx, "AsyncClient", FakeClient)

    response = await admin_client.get("/api/admin/curriculum/dictionary/lookup?word=reservation&lang=en&def_lang=vi")

    assert response.status_code == 200
    assert response.json()["meaning_vi"] == "sự đặt trước"
    assert response.json()["ipa"] == "/rezərˈveɪʃən/"
    assert response.json()["audio_url"] == "/api/curriculum/dictionary/audio?word=reservation&lang=en"


@pytest.mark.asyncio
async def test_admin_reorder_swaps_without_unique_constraint_error(admin_client, db_session):
    section = LearningSection(code="REORDER", title="Reorder", order_index=0)
    db_session.add(section)
    await db_session.flush()
    unit_1 = Unit(section_id=section.id, title="First", order_index=0)
    unit_2 = Unit(section_id=section.id, title="Second", order_index=1)
    db_session.add_all([unit_1, unit_2])
    await db_session.flush()
    lesson_1 = Lesson(
        unit_id=unit_1.id,
        type="sentence_pronunciation",
        title="One",
        order_index=0,
        content={"reference_text": "One"},
    )
    lesson_2 = Lesson(
        unit_id=unit_1.id,
        type="sentence_pronunciation",
        title="Two",
        order_index=1,
        content={"reference_text": "Two"},
    )
    db_session.add_all([lesson_1, lesson_2])
    await db_session.commit()

    unit_response = await admin_client.post(
        "/api/admin/curriculum/units/reorder",
        json={"items": [{"id": unit_2.id, "order_index": 0}, {"id": unit_1.id, "order_index": 1}]},
    )
    assert unit_response.status_code == 204

    lesson_response = await admin_client.post(
        "/api/admin/curriculum/lessons/reorder",
        json={"items": [{"id": lesson_2.id, "order_index": 0}, {"id": lesson_1.id, "order_index": 1}]},
    )
    assert lesson_response.status_code == 204

    await db_session.refresh(unit_1)
    await db_session.refresh(unit_2)
    await db_session.refresh(lesson_1)
    await db_session.refresh(lesson_2)
    assert unit_1.order_index == 1
    assert unit_2.order_index == 0
    assert lesson_1.order_index == 1
    assert lesson_2.order_index == 0

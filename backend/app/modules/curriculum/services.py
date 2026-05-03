from __future__ import annotations

import base64
import difflib
import io
import os
import re
import tempfile
import uuid
import wave
from datetime import date, datetime, timezone
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi.responses import Response
from sqlalchemy import Select, String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, UpstreamServiceError
from app.infra.supabase_storage import supabase_storage
from app.infra.contracts import TTSConfig
from app.infra.factory import create_tts
from app.modules.curriculum.models import (
    DictionaryAudioCache,
    LearningSection,
    Lesson,
    LessonAudioAsset,
    LessonAttempt,
    Unit,
    UserLessonProgress,
    UserUnitProgress,
)
from app.modules.curriculum.schemas import (
    LearningSectionCreate,
    LearningSectionUpdate,
    LessonAttemptRead,
    LessonAttemptRequest,
    LessonAudioTTSRequest,
    LessonCreate,
    LessonUpdate,
    ProgressSummary,
    ReorderRequest,
    StartConversationLessonRequest,
    StartConversationLessonResponse,
    UnitCreate,
    UnitUpdate,
    _validate_lesson_content,
)
from app.modules.sessions.schemas.session import SessionCreate
from app.modules.sessions.services.session import SessionService
from app.modules.users.models.user import User


WORD_RE = re.compile(r"[a-z0-9']+")
MAX_PRONUNCIATION_AUDIO_BYTES = 10 * 1024 * 1024
LESSON_AUDIO_UPLOAD_DIR = os.path.join("static", "uploads", "lesson-audio")
LESSON_AUDIO_URL_PREFIX = "/static/uploads/lesson-audio"
MIN_PRONUNCIATION_SAMPLE_RATE = 16000


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> date:
    return _utcnow().date()


def _normalize_word(value: str) -> str:
    return " ".join(WORD_RE.findall((value or "").lower())).strip()


def _truthy(column):
    return or_(
        column.is_(True),
        func.lower(cast(column, String)).in_(("true", "1", "t", "yes", "y", "on")),
    )


def _normalize_answer(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(WORD_RE.findall(value.lower())).strip()
    return " ".join(WORD_RE.findall(str(value).lower())).strip()


def _score_similarity(reference: str, answer: str) -> float:
    reference_norm = _normalize_answer(reference)
    answer_norm = _normalize_answer(answer)
    if not reference_norm or not answer_norm:
        return 0.0
    if reference_norm == answer_norm:
        return 100.0
    return round(difflib.SequenceMatcher(None, reference_norm, answer_norm).ratio() * 100, 2)


def _strip_data_url(value: str) -> str:
    if "," in value and value.split(",", 1)[0].startswith("data:"):
        return value.split(",", 1)[1]
    return value


def _decode_audio_base64(value: str | None) -> bytes | None:
    if not value:
        return None
    try:
        audio_bytes = base64.b64decode(_strip_data_url(value), validate=False)
    except Exception as exc:
        raise BadRequestError("Invalid audio_base64 payload") from exc
    if not audio_bytes:
        raise BadRequestError("Audio payload is empty")
    if len(audio_bytes) > MAX_PRONUNCIATION_AUDIO_BYTES:
        raise BadRequestError("Audio payload is too large")
    return audio_bytes


def _validate_wav_audio(audio_bytes: bytes) -> None:
    try:
        with wave.open(io.BytesIO(audio_bytes), "rb") as wav_file:
            channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            sample_rate = wav_file.getframerate()
            frame_count = wav_file.getnframes()
    except wave.Error as exc:
        raise BadRequestError("Audio must be a valid WAV file") from exc

    if channels != 1:
        raise BadRequestError("Audio must be mono WAV")
    if sample_width != 2:
        raise BadRequestError("Audio must be 16-bit PCM WAV")
    if sample_rate < MIN_PRONUNCIATION_SAMPLE_RATE:
        raise BadRequestError(f"Audio sample rate must be at least {MIN_PRONUNCIATION_SAMPLE_RATE} Hz")
    if frame_count <= 0:
        raise BadRequestError("Audio duration is empty")


class DictionaryApiService:
    source = "dict.minhqnd.com"

    @staticmethod
    def _language(value: str | None) -> str:
        language = (value or "en").strip().lower()
        if not re.fullmatch(r"[a-z]{2,10}(-[a-z0-9]{2,10})?", language):
            raise BadRequestError("Invalid dictionary language")
        return language

    @classmethod
    async def get_audio_response(cls, db: AsyncSession, *, word: str, language: str | None = None) -> Response:
        cache = await cls.get_or_fetch_audio(db, word=word, language=language)
        return Response(
            content=cache.audio_bytes,
            media_type=cache.content_type or "audio/wav",
            headers={
                "X-Dictionary-Source": cls.source,
                "Cache-Control": "public, max-age=604800",
            },
        )

    @classmethod
    async def lookup_word(
        cls,
        *,
        word: str,
        language: str | None = None,
        definition_language: str | None = None,
    ) -> dict[str, Any]:
        normalized = _normalize_word(word)
        if not normalized:
            raise BadRequestError("Word is required")
        lang = cls._language(language)
        def_lang = cls._language(definition_language or "vi")

        base_url = str(settings.dictionary_api_base_url).rstrip("/")
        source_url = f"{base_url}/api/v1/lookup"
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(
                    source_url,
                    params={"word": normalized, "lang": lang, "def_lang": def_lang},
                )
                response.raise_for_status()
                payload = response.json()
        except Exception as exc:
            raise UpstreamServiceError("Unable to look up dictionary word") from exc

        results = payload.get("results") if isinstance(payload, dict) else []
        result = next(
            (item for item in results or [] if isinstance(item, dict) and item.get("lang_code") == lang),
            None,
        )
        if result is None and results:
            result = next((item for item in results if isinstance(item, dict)), None)

        meanings = result.get("meanings") if isinstance(result, dict) else []
        definitions = [
            str(item.get("definition")).strip()
            for item in meanings or []
            if isinstance(item, dict)
            and item.get("definition_lang") == def_lang
            and str(item.get("definition") or "").strip()
        ]

        if not definitions and isinstance(result, dict):
            translations = result.get("translations") or []
            definitions = [
                str(item.get("translation")).strip()
                for item in translations
                if isinstance(item, dict)
                and item.get("lang_code") == def_lang
                and str(item.get("translation") or "").strip()
            ]

        pronunciations = result.get("pronunciations") if isinstance(result, dict) else []
        ipa = next(
            (
                str(item.get("ipa")).strip()
                for item in pronunciations or []
                if isinstance(item, dict) and str(item.get("ipa") or "").strip()
            ),
            None,
        )
        audio_query = urlencode({"word": normalized, "lang": lang})

        return {
            "word": normalized,
            "language": lang,
            "definition_language": def_lang,
            "meaning_vi": definitions[0] if definitions and def_lang == "vi" else None,
            "ipa": ipa,
            "audio_url": f"/api/curriculum/dictionary/audio?{audio_query}",
            "source": cls.source,
            "exists": bool(payload.get("exists")) if isinstance(payload, dict) else bool(definitions),
            "definitions": definitions,
        }

    @classmethod
    async def get_or_fetch_audio(
        cls,
        db: AsyncSession,
        *,
        word: str,
        language: str | None = None,
    ) -> DictionaryAudioCache:
        normalized = _normalize_word(word)
        if not normalized:
            raise BadRequestError("Word is required")
        lang = cls._language(language)

        cached = (
            await db.execute(
                select(DictionaryAudioCache).where(
                    DictionaryAudioCache.normalized_word == normalized,
                    DictionaryAudioCache.language == lang,
                )
            )
        ).scalar_one_or_none()
        if cached is not None:
            return cached

        base_url = str(settings.dictionary_api_base_url).rstrip("/")
        source_url = f"{base_url}/api/v1/tts"
        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                response = await client.get(source_url, params={"word": normalized, "lang": lang})
                response.raise_for_status()
        except Exception as exc:
            raise UpstreamServiceError("Unable to fetch dictionary audio") from exc

        content_type = response.headers.get("content-type", "audio/wav").split(";", 1)[0] or "audio/wav"
        if not response.content:
            raise UpstreamServiceError("Dictionary audio response was empty")

        cache = DictionaryAudioCache(
            normalized_word=normalized,
            language=lang,
            source=cls.source,
            source_url=str(response.url),
            content_type=content_type,
            audio_bytes=response.content,
            fetched_at=_utcnow(),
        )
        db.add(cache)
        await db.commit()
        await db.refresh(cache)
        return cache


class PronunciationAssessmentService:
    @staticmethod
    def _fallback(reference_text: str, fallback_answer: Any = None, source: str = "local_fallback") -> dict[str, Any]:
        score = _score_similarity(reference_text, fallback_answer) if fallback_answer else 0.0
        return {
            "score": score,
            "source": source,
            "accuracy_score": score,
            "pronunciation_score": score,
            "words": [],
        }

    @classmethod
    def assess(
        cls,
        *,
        reference_text: str,
        audio_bytes: bytes | None,
        fallback_answer: Any = None,
    ) -> dict[str, Any]:
        if not audio_bytes:
            return cls._fallback(reference_text, fallback_answer)
        if not settings.azure_speech_key or not settings.azure_speech_region:
            return cls._fallback(reference_text, fallback_answer, source="local_fallback_missing_config")

        _validate_wav_audio(audio_bytes)

        try:
            import azure.cognitiveservices.speech as speechsdk
        except Exception as exc:
            raise UpstreamServiceError("Azure Speech SDK is not installed") from exc

        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_bytes)
                temp_path = temp_file.name

            speech_config = speechsdk.SpeechConfig(
                subscription=settings.azure_speech_key,
                region=settings.azure_speech_region,
            )
            speech_config.speech_recognition_language = settings.azure_speech_language or "en-US"
            audio_config = speechsdk.AudioConfig(filename=temp_path)
            pronunciation_config = speechsdk.PronunciationAssessmentConfig(
                reference_text=reference_text,
                grading_system=speechsdk.PronunciationAssessmentGradingSystem.HundredMark,
                granularity=speechsdk.PronunciationAssessmentGranularity.Phoneme,
                enable_miscue=True,
            )
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            pronunciation_config.apply_to(recognizer)
            result = recognizer.recognize_once()
            if result.reason == speechsdk.ResultReason.Canceled:
                details = speechsdk.CancellationDetails(result)
                raise UpstreamServiceError(f"Azure pronunciation assessment canceled: {details.reason}")
            if result.reason == speechsdk.ResultReason.NoMatch:
                raise BadRequestError("Azure Speech could not recognize speech in the recording")
            assessment = speechsdk.PronunciationAssessmentResult(result)
            json_result = result.properties.get(
                speechsdk.PropertyId.SpeechServiceResponse_JsonResult,
                "{}",
            )
            score = float(assessment.pronunciation_score or assessment.accuracy_score or 0)
            return {
                "score": round(score, 2),
                "source": "azure",
                "accuracy_score": float(assessment.accuracy_score or 0),
                "fluency_score": float(assessment.fluency_score or 0),
                "completeness_score": float(assessment.completeness_score or 0),
                "pronunciation_score": float(assessment.pronunciation_score or 0),
                "raw": json_result,
            }
        except (BadRequestError, UpstreamServiceError):
            raise
        except Exception as exc:
            raise UpstreamServiceError("Azure pronunciation assessment failed") from exc
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass


class CurriculumService:
    @staticmethod
    def _active_sections_stmt(*, include_lessons: bool = False) -> Select[tuple[LearningSection]]:
        units_loader = selectinload(LearningSection.units)
        if include_lessons:
            units_loader = units_loader.selectinload(Unit.lessons)
        return (
            select(LearningSection)
            .options(units_loader)
            .where(_truthy(LearningSection.is_active))
            .order_by(LearningSection.order_index.asc(), LearningSection.id.asc())
        )

    @staticmethod
    def _flatten_units(sections: list[LearningSection]) -> list[Unit]:
        units: list[Unit] = []
        for section in sorted(sections, key=lambda item: (item.order_index, item.id)):
            for unit in sorted(section.units, key=lambda item: (item.order_index, item.id)):
                if unit.is_active:
                    units.append(unit)
        return units

    @classmethod
    async def curriculum_tree(
        cls,
        db: AsyncSession,
        user_id: int,
        *,
        include_lessons: bool = False,
        include_lesson_progress: bool = False,
    ) -> tuple[list[LearningSection], dict[int, UserUnitProgress], dict[int, UserLessonProgress], set[int], int | None]:
        include_lessons = include_lessons or include_lesson_progress
        sections = list((await db.execute(cls._active_sections_stmt(include_lessons=include_lessons))).scalars().unique().all())
        units = cls._flatten_units(sections)
        unit_ids = [unit.id for unit in units]
        lesson_ids = [
            lesson.id
            for unit in units
            for lesson in unit.__dict__.get("lessons", [])
            if lesson.is_active
        ] if include_lesson_progress else []

        unit_progress = {}
        if unit_ids:
            rows = (
                await db.execute(
                    select(UserUnitProgress).where(
                        UserUnitProgress.user_id == user_id,
                        UserUnitProgress.unit_id.in_(unit_ids),
                    )
                )
            ).scalars().all()
            unit_progress = {item.unit_id: item for item in rows}

        lesson_progress = {}
        if lesson_ids:
            rows = (
                await db.execute(
                    select(UserLessonProgress).where(
                        UserLessonProgress.user_id == user_id,
                        UserLessonProgress.lesson_id.in_(lesson_ids),
                    )
                )
            ).scalars().all()
            lesson_progress = {item.lesson_id: item for item in rows}

        completed_so_far = True
        unlocked: set[int] = set()
        current_unit_id: int | None = None
        for unit in units:
            if completed_so_far:
                unlocked.add(unit.id)
                progress = unit_progress.get(unit.id)
                if current_unit_id is None and (progress is None or progress.status != "completed"):
                    current_unit_id = unit.id
                completed_so_far = bool(progress and progress.status == "completed")

        return sections, unit_progress, lesson_progress, unlocked, current_unit_id

    @classmethod
    async def get_user_unit(
        cls,
        db: AsyncSession,
        *,
        user_id: int,
        unit_id: int,
    ) -> tuple[Unit, dict[int, UserLessonProgress], bool, UserUnitProgress | None]:
        sections, unit_progress, _, unlocked, _ = await cls.curriculum_tree(db, user_id)
        active_unit_ids = {item.id for item in cls._flatten_units(sections)}
        if unit_id not in active_unit_ids:
            raise NotFoundError("Unit not found")
        is_unlocked = unit_id in unlocked
        if not is_unlocked:
            raise ForbiddenError("Complete previous units before opening this unit")

        unit = (
            await db.execute(
                select(Unit)
                .options(selectinload(Unit.lessons))
                .where(Unit.id == unit_id, _truthy(Unit.is_active))
            )
        ).scalar_one_or_none()
        if unit is None:
            raise NotFoundError("Unit not found")

        lesson_ids = [lesson.id for lesson in unit.lessons if lesson.is_active]
        lesson_progress = {}
        if lesson_ids:
            rows = (
                await db.execute(
                    select(UserLessonProgress).where(
                        UserLessonProgress.user_id == user_id,
                        UserLessonProgress.lesson_id.in_(lesson_ids),
                    )
                )
            ).scalars().all()
            lesson_progress = {item.lesson_id: item for item in rows}
        return unit, lesson_progress, is_unlocked, unit_progress.get(unit.id)

    @classmethod
    async def attempt_lesson(
        cls,
        db: AsyncSession,
        *,
        user: User,
        lesson_id: int,
        payload: LessonAttemptRequest,
    ) -> LessonAttemptRead:
        lesson = await cls._get_active_lesson(db, lesson_id, include_unit_lessons=False)
        await cls.get_user_unit(db, user_id=user.id, unit_id=lesson.unit_id)

        score, feedback, answer_payload = await cls._score_lesson(db, user=user, lesson=lesson, payload=payload)
        target_passed = score >= lesson.pass_score
        attempt = LessonAttempt(
            user_id=user.id,
            lesson_id=lesson.id,
            answer=answer_payload,
            audio_url=payload.audio_url,
            score=score,
            passed=target_passed,
            attempt_metadata=feedback,
        )
        db.add(attempt)
        await db.flush()

        progress = await cls._get_or_create_lesson_progress(db, user.id, lesson.id)
        progress.attempt_count = (progress.attempt_count or 0) + 1
        progress.best_score = max(progress.best_score or 0, score)
        progress.state = cls._merge_progress_state(
            lesson=lesson,
            progress=progress,
            feedback=feedback,
            target_passed=target_passed,
        )
        lesson_passed = cls._lesson_is_completed(lesson=lesson, state=progress.state, target_passed=target_passed)
        progress.status = "completed" if lesson_passed else "in_progress"
        attempt.passed = lesson_passed

        unit_completed, reward = await cls._refresh_unit_progress(db, user=user, unit_id=lesson.unit_id)
        await db.commit()
        return LessonAttemptRead(
            id=attempt.id,
            lesson_id=lesson.id,
            score=score,
            passed=lesson_passed,
            feedback=feedback,
            progress=cls._progress_summary(progress),
            unit_completed=unit_completed,
            reward=reward.model_dump(mode="json") if reward else None,
        )

    @classmethod
    async def _score_lesson(
        cls,
        db: AsyncSession,
        *,
        user: User,
        lesson: Lesson,
        payload: LessonAttemptRequest,
    ) -> tuple[float, dict[str, Any], Any]:
        content = lesson.content or {}
        if lesson.type == "cloze_dictation":
            return cls._score_cloze(content, payload.answer)
        if lesson.type == "vocab_pronunciation":
            return await cls._score_vocab_pronunciation(content, payload)
        if lesson.type == "sentence_pronunciation":
            return cls._score_sentence_pronunciation(content, payload)
        if lesson.type == "interactive_conversation":
            return await cls._score_conversation(db, user=user, lesson=lesson, payload=payload)
        if lesson.type == "word_audio_choice":
            return cls._score_word_audio_choice(content, payload.answer)
        raise BadRequestError("Unsupported lesson type")

    @staticmethod
    def _score_cloze(content: dict[str, Any], answer: Any) -> tuple[float, dict[str, Any], Any]:
        submitted = answer if isinstance(answer, dict) else {}
        submitted_blanks = submitted.get("blanks") or submitted.get("answers") or answer or []
        if isinstance(submitted_blanks, dict):
            submitted_values = submitted_blanks
        elif isinstance(submitted_blanks, list):
            submitted_values = {str(index): value for index, value in enumerate(submitted_blanks)}
        else:
            submitted_values = {}

        blanks = content.get("blanks") or []
        results = []
        correct = 0
        for index, blank in enumerate(blanks):
            accepted = [blank.get("answer"), *(blank.get("accepted_answers") or [])]
            accepted_norm = {_normalize_answer(item) for item in accepted if item}
            value = submitted_values.get(str(index), submitted_values.get(index, ""))
            value_norm = _normalize_answer(value)
            is_correct = bool(value_norm and value_norm in accepted_norm)
            correct += 1 if is_correct else 0
            results.append(
                {
                    "index": index,
                    "submitted": value,
                    "correct": is_correct,
                    "answer": blank.get("answer"),
                    "meaning_vi": blank.get("meaning_vi"),
                    "explanation_vi": None if is_correct else blank.get("explanation_vi"),
                }
            )
        score = round((correct / len(blanks)) * 100, 2) if blanks else 0
        return score, {"blank_results": results, "correct": correct, "total": len(blanks)}, submitted

    @staticmethod
    async def _score_vocab_pronunciation(
        content: dict[str, Any],
        payload: LessonAttemptRequest,
    ) -> tuple[float, dict[str, Any], Any]:
        submitted = payload.answer if isinstance(payload.answer, dict) else {}
        target_word = submitted.get("word") or submitted.get("target_word")
        words = content.get("words") or []
        if not target_word and words:
            target_word = words[0].get("word") if isinstance(words[0], dict) else str(words[0])
        if not target_word:
            raise BadRequestError("Vocabulary pronunciation attempt requires a target word")

        audio_bytes = _decode_audio_base64(payload.audio_base64)
        assessment = PronunciationAssessmentService.assess(
            reference_text=str(target_word),
            audio_bytes=audio_bytes,
            fallback_answer=submitted.get("transcript"),
        )
        score = round(float(assessment.get("score") or 0), 2)
        attempted_words = {str(target_word)}
        failed_words = []
        for word_item in words:
            word = word_item.get("word") if isinstance(word_item, dict) else str(word_item)
            if word in attempted_words and score < float(content.get("pass_score") or 80):
                failed_words.append(word)
        return score, {"target_word": target_word, "assessment": assessment, "failed_words": failed_words}, submitted

    @staticmethod
    def _score_sentence_pronunciation(
        content: dict[str, Any],
        payload: LessonAttemptRequest,
    ) -> tuple[float, dict[str, Any], Any]:
        reference_text = str(content.get("reference_text") or "").strip()
        if not reference_text:
            raise BadRequestError("Sentence pronunciation lesson has no reference_text")
        submitted = payload.answer if isinstance(payload.answer, dict) else {"transcript": payload.answer}
        audio_bytes = _decode_audio_base64(payload.audio_base64)
        assessment = PronunciationAssessmentService.assess(
            reference_text=reference_text,
            audio_bytes=audio_bytes,
            fallback_answer=submitted.get("transcript") if isinstance(submitted, dict) else submitted,
        )
        score = round(float(assessment.get("score") or 0), 2)
        return score, {"reference_text": reference_text, "assessment": assessment}, submitted

    @staticmethod
    async def _score_conversation(
        db: AsyncSession,
        *,
        user: User,
        lesson: Lesson,
        payload: LessonAttemptRequest,
    ) -> tuple[float, dict[str, Any], Any]:
        if payload.session_id is None:
            raise BadRequestError("interactive_conversation attempt requires session_id")
        session = await SessionService.get_by_id(db, payload.session_id, user.id)
        if session.status != "completed":
            raise BadRequestError("Conversation session must be completed before scoring")
        if not session.score:
            score = 0.0
        else:
            score = round(float(session.score.overall_score or 0) * 10, 2)
        return score, {"session_id": session.id, "overall_score": score}, {"session_id": session.id}

    @staticmethod
    def _score_word_audio_choice(content: dict[str, Any], answer: Any) -> tuple[float, dict[str, Any], Any]:
        submitted = answer if isinstance(answer, dict) else {}
        selected_word = _normalize_word(str(submitted.get("selected_word") or submitted.get("word") or ""))
        options = content.get("options") or []
        correct_option = next((item for item in options if isinstance(item, dict) and item.get("is_correct") is True), None)
        if not correct_option:
            raise BadRequestError("word_audio_choice lesson is missing a correct option")
        correct_word = _normalize_word(str(correct_option.get("word") or ""))
        if not selected_word:
            raise BadRequestError("word_audio_choice attempt requires selected_word")
        passed = selected_word == correct_word
        return (
            100.0 if passed else 0.0,
            {"selected_word": selected_word, "correct_word": correct_word, "correct": passed},
            submitted,
        )

    @staticmethod
    def _merge_progress_state(
        *,
        lesson: Lesson,
        progress: UserLessonProgress,
        feedback: dict[str, Any],
        target_passed: bool,
    ) -> dict[str, Any]:
        state = dict(progress.state or {})
        if lesson.type == "vocab_pronunciation":
            previous_failed = set(state.get("retry_words") or [])
            passed_words = set(state.get("passed_words") or [])
            target = feedback.get("target_word")
            if target and target_passed:
                previous_failed.discard(target)
                passed_words.add(target)
            elif target:
                previous_failed.add(target)
                passed_words.discard(target)
            all_words = [
                item.get("word") if isinstance(item, dict) else str(item)
                for item in (lesson.content or {}).get("words", [])
            ]
            for word in all_words:
                if word not in passed_words:
                    previous_failed.add(word)
            state["retry_words"] = sorted(previous_failed)
            state["passed_words"] = sorted(passed_words)
        state["last_feedback"] = feedback
        state["target_passed"] = target_passed
        return state

    @staticmethod
    def _lesson_is_completed(
        *,
        lesson: Lesson,
        state: dict[str, Any],
        target_passed: bool,
    ) -> bool:
        if not target_passed:
            return False
        if lesson.type != "vocab_pronunciation":
            return True
        words = [
            item.get("word") if isinstance(item, dict) else str(item)
            for item in (lesson.content or {}).get("words", [])
        ]
        passed_words = set(state.get("passed_words") or [])
        return bool(words) and all(word in passed_words for word in words)

    @classmethod
    async def start_conversation_lesson(
        cls,
        db: AsyncSession,
        *,
        user: User,
        lesson_id: int,
        payload: StartConversationLessonRequest,
    ) -> StartConversationLessonResponse:
        lesson = await cls._get_active_lesson(db, lesson_id)
        if lesson.type != "interactive_conversation":
            raise BadRequestError("Lesson is not an interactive conversation")
        await cls.get_user_unit(db, user_id=user.id, unit_id=lesson.unit_id)
        scenario_id = int((lesson.content or {}).get("scenario_id") or 0)
        if not scenario_id:
            raise BadRequestError("Conversation lesson is missing scenario_id")

        metadata = {
            **(payload.metadata or {}),
            "curriculum_mode": True,
            "unit_id": lesson.unit_id,
            "lesson_id": lesson.id,
        }
        session = await SessionService.start_session(
            db,
            user_id=user.id,
            user=user,
            payload=SessionCreate(
                scenario_id=scenario_id,
                metadata=metadata,
            ),
        )
        return StartConversationLessonResponse(
            session_id=session.id,
            scenario_id=scenario_id,
            result_url=f"/sessions/{session.id}/result",
            metadata=dict(session.session_metadata or {}),
        )

    @staticmethod
    async def _get_active_lesson(db: AsyncSession, lesson_id: int, *, include_unit_lessons: bool = True) -> Lesson:
        stmt = select(Lesson).where(Lesson.id == lesson_id, _truthy(Lesson.is_active))
        if include_unit_lessons:
            stmt = stmt.options(selectinload(Lesson.unit).selectinload(Unit.lessons))
        lesson = (await db.execute(stmt)).scalar_one_or_none()
        if lesson is None:
            raise NotFoundError("Lesson not found")
        return lesson

    @staticmethod
    async def _get_or_create_lesson_progress(db: AsyncSession, user_id: int, lesson_id: int) -> UserLessonProgress:
        progress = (
            await db.execute(
                select(UserLessonProgress).where(
                    UserLessonProgress.user_id == user_id,
                    UserLessonProgress.lesson_id == lesson_id,
                )
            )
        ).scalar_one_or_none()
        if progress is None:
            progress = UserLessonProgress(user_id=user_id, lesson_id=lesson_id, status="not_started", state={})
            db.add(progress)
            await db.flush()
        return progress

    @staticmethod
    async def _get_or_create_unit_progress(db: AsyncSession, user_id: int, unit_id: int) -> UserUnitProgress:
        progress = (
            await db.execute(
                select(UserUnitProgress).where(
                    UserUnitProgress.user_id == user_id,
                    UserUnitProgress.unit_id == unit_id,
                )
            )
        ).scalar_one_or_none()
        if progress is None:
            progress = UserUnitProgress(user_id=user_id, unit_id=unit_id, status="not_started")
            db.add(progress)
            await db.flush()
        return progress

    @classmethod
    async def _refresh_unit_progress(cls, db: AsyncSession, *, user: User, unit_id: int) -> tuple[bool, Any | None]:
        unit = (
            await db.execute(
                select(Unit)
                .options(selectinload(Unit.lessons))
                .where(Unit.id == unit_id)
            )
        ).scalar_one()
        progress = await cls._get_or_create_unit_progress(db, user.id, unit.id)
        if progress.status == "not_started":
            progress.status = "in_progress"
            progress.started_at = progress.started_at or _utcnow()

        required_lessons = [item for item in unit.lessons if item.is_active and item.is_required]
        if not required_lessons:
            return False, None
        rows = (
            await db.execute(
                select(UserLessonProgress).where(
                    UserLessonProgress.user_id == user.id,
                    UserLessonProgress.lesson_id.in_([item.id for item in required_lessons]),
                )
            )
        ).scalars().all()
        by_lesson = {item.lesson_id: item for item in rows}
        completed = all(by_lesson.get(item.id) and by_lesson[item.id].status == "completed" for item in required_lessons)
        scores = [by_lesson[item.id].best_score or 0 for item in required_lessons if by_lesson.get(item.id)]
        progress.best_score = round(sum(scores) / len(scores), 2) if scores else None
        reward = None
        if completed and progress.status != "completed":
            progress.status = "completed"
            progress.completed_at = _utcnow()
            cls._update_user_completion_counters(user, unit, progress.best_score)
            from app.modules.gamification.services import GamificationService

            reward = await GamificationService.award_lesson_completion(db, user=user, lesson=unit)
        return completed, reward

    @staticmethod
    def _update_user_completion_counters(user: User, unit: Unit, score: float | None) -> None:
        lesson_types = {lesson.type for lesson in unit.lessons}
        if lesson_types & {"vocab_pronunciation", "word_audio_choice"}:
            user.total_vocabulary_lessons_completed = (user.total_vocabulary_lessons_completed or 0) + 1
        if lesson_types & {"sentence_pronunciation", "interactive_conversation"}:
            user.total_speaking_lessons_completed = (user.total_speaking_lessons_completed or 0) + 1
        if score is not None and score >= 90:
            user.perfect_score_count = (user.perfect_score_count or 0) + 1

    @staticmethod
    def _progress_summary(progress: UserLessonProgress | None) -> ProgressSummary:
        if progress is None:
            return ProgressSummary()
        return ProgressSummary(
            status=progress.status,
            best_score=progress.best_score,
            attempt_count=progress.attempt_count or 0,
            state=dict(progress.state or {}),
        )


class AdminCurriculumService:
    @staticmethod
    def _lesson_audio_path(filename: str) -> tuple[str, str]:
        os.makedirs(LESSON_AUDIO_UPLOAD_DIR, exist_ok=True)
        return os.path.join(LESSON_AUDIO_UPLOAD_DIR, filename), f"{LESSON_AUDIO_URL_PREFIX}/{filename}"

    @staticmethod
    async def _upload_lesson_audio_to_storage(
        *,
        filename: str,
        audio_bytes: bytes,
        content_type: str,
    ) -> str:
        if not supabase_storage.is_configured:
            filepath, url = AdminCurriculumService._lesson_audio_path(filename)
            with open(filepath, "wb") as audio_file:
                audio_file.write(audio_bytes)
            return url

        result = await supabase_storage.upload_public_object(
            bucket=settings.supabase_audio_bucket,
            path=f"lesson-audio/{filename}",
            content=audio_bytes,
            content_type=content_type,
        )
        return result.public_url

    @staticmethod
    async def _create_audio_asset(
        db: AsyncSession,
        *,
        source: str,
        audio_bytes: bytes,
        content_type: str,
        lesson_id: int | None = None,
        text: str | None = None,
        voice: str | None = None,
        language: str | None = None,
        extension: str = "wav",
    ) -> LessonAudioAsset:
        if lesson_id is not None:
            await AdminCurriculumService.get_lesson(db, lesson_id)
        if not audio_bytes:
            raise BadRequestError("Lesson audio was empty")
        if len(audio_bytes) > settings.lesson_audio_upload_max_bytes:
            raise BadRequestError("Lesson audio exceeds maximum size")

        safe_extension = re.sub(r"[^a-zA-Z0-9]", "", extension or "wav")[:12] or "wav"
        filename = f"{uuid.uuid4().hex}.{safe_extension}"
        url = await AdminCurriculumService._upload_lesson_audio_to_storage(
            filename=filename,
            audio_bytes=audio_bytes,
            content_type=content_type,
        )

        asset = LessonAudioAsset(
            lesson_id=lesson_id,
            source=source,
            text=(text or None),
            voice=(voice or None),
            language=(language or None),
            filename=filename,
            url=url,
            content_type=content_type,
            size_bytes=len(audio_bytes),
        )
        db.add(asset)
        await db.commit()
        await db.refresh(asset)
        return asset

    @staticmethod
    async def create_tts_audio(db: AsyncSession, body: LessonAudioTTSRequest) -> LessonAudioAsset:
        text = body.text.strip()
        if not text:
            raise BadRequestError("TTS text is required")
        voice = (body.voice or settings.tts_voice or "Cherry").strip()
        language = (body.language or "en").strip()
        tts = create_tts(settings)
        chunks: list[bytes] = []
        try:
            async for chunk in tts.synthesize(text, TTSConfig(voice=voice, language=language)):
                if chunk:
                    chunks.append(chunk)
        finally:
            await tts.close()
        return await AdminCurriculumService._create_audio_asset(
            db,
            source="tts",
            audio_bytes=b"".join(chunks),
            content_type="audio/wav",
            lesson_id=body.lesson_id,
            text=text,
            voice=voice,
            language=language,
            extension="wav",
        )

    @staticmethod
    async def upload_audio(
        db: AsyncSession,
        *,
        audio_bytes: bytes,
        filename: str | None,
        content_type: str | None,
        lesson_id: int | None = None,
        text: str | None = None,
        language: str | None = None,
    ) -> LessonAudioAsset:
        normalized_content_type = (content_type or "").split(";", 1)[0].strip().lower()
        if not normalized_content_type.startswith("audio/"):
            raise BadRequestError("Uploaded lesson audio must be an audio file")
        extension = os.path.splitext(filename or "")[1].lstrip(".") or normalized_content_type.split("/", 1)[1]
        return await AdminCurriculumService._create_audio_asset(
            db,
            source="upload",
            audio_bytes=audio_bytes,
            content_type=normalized_content_type,
            lesson_id=lesson_id,
            text=(text or "").strip() or None,
            language=(language or "").strip() or None,
            extension=extension,
        )

    @staticmethod
    async def list_sections(db: AsyncSession, include_inactive: bool = True) -> list[LearningSection]:
        stmt = select(LearningSection).options(selectinload(LearningSection.units).selectinload(Unit.lessons))
        if not include_inactive:
            stmt = stmt.where(_truthy(LearningSection.is_active))
        stmt = stmt.order_by(LearningSection.order_index.asc(), LearningSection.id.asc())
        return list((await db.execute(stmt)).scalars().unique().all())

    @staticmethod
    async def create_section(db: AsyncSession, body: LearningSectionCreate) -> LearningSection:
        section = LearningSection(**body.model_dump())
        db.add(section)
        await db.commit()
        await db.refresh(section)
        return section

    @staticmethod
    async def update_section(db: AsyncSession, section_id: int, body: LearningSectionUpdate) -> LearningSection:
        section = await AdminCurriculumService.get_section(db, section_id)
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(section, key, value)
        await db.commit()
        await db.refresh(section)
        return section

    @staticmethod
    async def get_section(db: AsyncSession, section_id: int) -> LearningSection:
        section = (
            await db.execute(
                select(LearningSection)
                .options(selectinload(LearningSection.units).selectinload(Unit.lessons))
                .where(LearningSection.id == section_id)
            )
        ).scalar_one_or_none()
        if section is None:
            raise NotFoundError("Section not found")
        return section

    @staticmethod
    async def delete_section(db: AsyncSession, section_id: int) -> LearningSection:
        section = await AdminCurriculumService.get_section(db, section_id)
        section.is_active = False
        await db.commit()
        return section

    @staticmethod
    async def create_unit(db: AsyncSession, body: UnitCreate) -> Unit:
        await AdminCurriculumService.get_section(db, body.section_id)
        unit = Unit(**body.model_dump())
        db.add(unit)
        await db.commit()
        await db.refresh(unit)
        return unit

    @staticmethod
    async def update_unit(db: AsyncSession, unit_id: int, body: UnitUpdate) -> Unit:
        unit = await AdminCurriculumService.get_unit(db, unit_id)
        if body.section_id is not None:
            await AdminCurriculumService.get_section(db, body.section_id)
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(unit, key, value)
        await db.commit()
        await db.refresh(unit)
        return unit

    @staticmethod
    async def get_unit(db: AsyncSession, unit_id: int) -> Unit:
        unit = (
            await db.execute(
                select(Unit)
                .options(selectinload(Unit.lessons))
                .where(Unit.id == unit_id)
            )
        ).scalar_one_or_none()
        if unit is None:
            raise NotFoundError("Unit not found")
        return unit

    @staticmethod
    async def delete_unit(db: AsyncSession, unit_id: int) -> Unit:
        unit = await AdminCurriculumService.get_unit(db, unit_id)
        unit.is_active = False
        await db.commit()
        return unit

    @staticmethod
    async def create_lesson(db: AsyncSession, body: LessonCreate) -> Lesson:
        unit = await AdminCurriculumService.get_unit(db, body.unit_id)
        data = body.model_dump()
        existing_lessons = unit.lessons or []
        data["title"] = (data.get("title") or "").strip() or f"Lesson {len(existing_lessons) + 1}"
        if "order_index" not in body.model_fields_set:
            data["order_index"] = max((lesson.order_index for lesson in existing_lessons), default=-1) + 1
        lesson = Lesson(**data)
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    @staticmethod
    async def update_lesson(db: AsyncSession, lesson_id: int, body: LessonUpdate) -> Lesson:
        lesson = await AdminCurriculumService.get_lesson(db, lesson_id)
        data = body.model_dump(exclude_unset=True)
        if "unit_id" in data:
            await AdminCurriculumService.get_unit(db, int(data["unit_id"]))
        if "content" in data:
            _validate_lesson_content(str(data.get("type") or lesson.type), data["content"])
        for key, value in data.items():
            setattr(lesson, key, value)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    @staticmethod
    async def get_lesson(db: AsyncSession, lesson_id: int) -> Lesson:
        lesson = (await db.execute(select(Lesson).where(Lesson.id == lesson_id))).scalar_one_or_none()
        if lesson is None:
            raise NotFoundError("Lesson not found")
        return lesson

    @staticmethod
    async def delete_lesson(db: AsyncSession, lesson_id: int) -> Lesson:
        lesson = await AdminCurriculumService.get_lesson(db, lesson_id)
        lesson.is_active = False
        await db.commit()
        return lesson

    @staticmethod
    async def reorder(db: AsyncSession, *, model: type, body: ReorderRequest) -> None:
        ids = [item.id for item in body.items]
        rows = list((await db.execute(select(model).where(model.id.in_(ids)))).scalars().all())
        by_id = {item.id: item for item in rows}
        missing_ids = [item_id for item_id in ids if item_id not in by_id]
        if missing_ids:
            raise NotFoundError("Curriculum item not found")

        max_order = (await db.execute(select(func.max(model.order_index)))).scalar() or 0
        temporary_base = int(max_order) + len(rows) + 1000
        for offset, row in enumerate(rows):
            row.order_index = temporary_base + offset
        await db.flush()

        for item in body.items:
            by_id[item.id].order_index = item.order_index
        await db.commit()

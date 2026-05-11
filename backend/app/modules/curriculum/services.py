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
from sqlalchemy import Select, String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, UpstreamServiceError
from app.infra.supabase_storage import supabase_storage
from app.infra.contracts import TTSConfig
from app.infra.factory import create_tts
from app.modules.curriculum.models import (
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
    UnitCreate,
    UnitUpdate,
    VALID_LESSON_TYPES,
    _validate_lesson_content,
)
from app.modules.users.models.user import User


WORD_RE = re.compile(r"[a-z0-9']+")
MAX_PRONUNCIATION_AUDIO_BYTES = 10 * 1024 * 1024
LESSON_AUDIO_UPLOAD_DIR = os.path.join("static", "uploads", "lesson-audio")
LESSON_AUDIO_URL_PREFIX = "/static/uploads/lesson-audio"
MIN_PRONUNCIATION_SAMPLE_RATE = 16000
CEFR_ORDER = {"A1": 0, "A2": 1, "B1": 2, "B2": 3, "C1": 4, "C2": 5}


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> date:
    return _utcnow().date()


def _normalize_cefr_level(value: str | None) -> str:
    if not value:
        return "A1"
    normalized = value.strip()
    return normalized.upper()


def _cefr_rank(value: str | None) -> int:
    return CEFR_ORDER.get(_normalize_cefr_level(value), CEFR_ORDER["A1"])


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

class SpeechTranscriptionService:
    @classmethod
    def transcribe(cls, *, audio_bytes: bytes | None, fallback_answer: Any = None) -> dict[str, Any]:
        fallback_text = ""
        if isinstance(fallback_answer, dict):
            fallback_text = str(fallback_answer.get("transcript") or fallback_answer.get("text") or "").strip()
        elif fallback_answer is not None:
            fallback_text = str(fallback_answer).strip()
        if not audio_bytes:
            return {"transcript": fallback_text, "source": "fallback_no_audio"}
        if not settings.azure_speech_key or not settings.azure_speech_region:
            return {"transcript": fallback_text, "source": "fallback_missing_config"}

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
            recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
            result = recognizer.recognize_once()
            if result.reason == speechsdk.ResultReason.Canceled:
                details = speechsdk.CancellationDetails(result)
                raise UpstreamServiceError(f"Azure speech recognition canceled: {details.reason}")
            if result.reason == speechsdk.ResultReason.NoMatch:
                return {"transcript": fallback_text, "source": "azure_no_match"}
            return {"transcript": str(result.text or "").strip(), "source": "azure"}
        except UpstreamServiceError:
            raise
        except Exception as exc:
            raise UpstreamServiceError("Azure speech recognition failed") from exc
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
        user_cefr: str | None = None,
        include_lessons: bool = False,
        include_lesson_progress: bool = False,
    ) -> tuple[list[LearningSection], dict[int, UserUnitProgress], dict[int, UserLessonProgress], set[int], int | None]:
        include_lessons = include_lessons or include_lesson_progress
        sections = list((await db.execute(cls._active_sections_stmt(include_lessons=include_lessons))).scalars().unique().all())
        units = cls._flatten_units(sections)
        unit_cefr_levels = {
            unit.id: section.cefr_level
            for section in sections
            for unit in section.__dict__.get("units", [])
        }
        unit_ids = [unit.id for unit in units]
        lesson_ids = [
            lesson.id
            for unit in units
            for lesson in unit.__dict__.get("lessons", [])
            if lesson.is_active and lesson.type in VALID_LESSON_TYPES
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

        start_rank = _cefr_rank(user_cefr)
        completed_so_far = True
        unlocked: set[int] = set()
        current_unit_id: int | None = None
        for unit in units:
            unit_rank = _cefr_rank(unit_cefr_levels.get(unit.id))
            if unit_rank < start_rank:
                unlocked.add(unit.id)
                continue

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
        user: User,
        unit_id: int,
    ) -> tuple[Unit, dict[int, UserLessonProgress], bool, UserUnitProgress | None]:
        sections, unit_progress, _, unlocked, _ = await cls.curriculum_tree(
            db,
            user.id,
            user_cefr=user.current_cefr or user.level,
        )
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

        lesson_ids = [lesson.id for lesson in unit.lessons if lesson.is_active and lesson.type in VALID_LESSON_TYPES]
        lesson_progress = {}
        if lesson_ids:
            rows = (
                await db.execute(
                    select(UserLessonProgress).where(
                        UserLessonProgress.user_id == user.id,
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
        await cls.get_user_unit(db, user=user, unit_id=lesson.unit_id)

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
        if lesson.type == "shadowing":
            return cls._score_shadowing(content, payload)
        if lesson.type == "read_aloud":
            return cls._score_read_aloud(content, payload)
        if lesson.type == "definition_choice":
            return cls._score_definition_choice(content, payload.answer)
        if lesson.type == "quick_qa":
            return cls._score_quick_qa(content, payload)
        raise BadRequestError("Unsupported lesson type")

    @staticmethod
    def _score_pronunciation_lesson(
        *,
        reference_text: str,
        payload: LessonAttemptRequest,
        missing_message: str,
    ) -> tuple[float, dict[str, Any], Any]:
        reference = str(reference_text or "").strip()
        if not reference:
            raise BadRequestError(missing_message)
        submitted = payload.answer if isinstance(payload.answer, dict) else {"transcript": payload.answer}
        audio_bytes = _decode_audio_base64(payload.audio_base64)
        assessment = PronunciationAssessmentService.assess(
            reference_text=reference,
            audio_bytes=audio_bytes,
            fallback_answer=submitted.get("transcript") if isinstance(submitted, dict) else submitted,
        )
        score = round(float(assessment.get("score") or 0), 2)
        return score, {"reference_text": reference, "assessment": assessment}, submitted

    @classmethod
    def _score_shadowing(cls, content: dict[str, Any], payload: LessonAttemptRequest) -> tuple[float, dict[str, Any], Any]:
        return cls._score_pronunciation_lesson(
            reference_text=str(content.get("reference_text") or ""),
            payload=payload,
            missing_message="shadowing lesson has no reference_text",
        )

    @classmethod
    def _score_read_aloud(cls, content: dict[str, Any], payload: LessonAttemptRequest) -> tuple[float, dict[str, Any], Any]:
        return cls._score_pronunciation_lesson(
            reference_text=str(content.get("text") or ""),
            payload=payload,
            missing_message="read_aloud lesson has no text",
        )

    @staticmethod
    def _score_definition_choice(content: dict[str, Any], answer: Any) -> tuple[float, dict[str, Any], Any]:
        submitted = answer if isinstance(answer, dict) else {}
        selected_word = _normalize_word(str(submitted.get("selected_word") or submitted.get("word") or ""))
        options = content.get("options") or []
        correct_option = next((item for item in options if isinstance(item, dict) and item.get("is_correct") is True), None)
        if not correct_option:
            raise BadRequestError("definition_choice lesson is missing a correct option")
        correct_word = _normalize_word(str(correct_option.get("word") or ""))
        if not selected_word:
            raise BadRequestError("definition_choice attempt requires selected_word")
        passed = selected_word == correct_word
        return (
            100.0 if passed else 0.0,
            {"selected_word": selected_word, "correct_word": correct_word, "correct": passed},
            submitted,
        )

    @staticmethod
    def _score_quick_qa(content: dict[str, Any], payload: LessonAttemptRequest) -> tuple[float, dict[str, Any], Any]:
        question_text = str(content.get("question_text") or "").strip()
        if not question_text:
            raise BadRequestError("quick_qa lesson has no question_text")
        min_words = int(content.get("min_words") or 2)
        audio_bytes = _decode_audio_base64(payload.audio_base64)
        submitted = payload.answer if isinstance(payload.answer, dict) else {"transcript": payload.answer}
        transcription = SpeechTranscriptionService.transcribe(audio_bytes=audio_bytes, fallback_answer=submitted)
        transcript = str(transcription.get("transcript") or "").strip()
        word_count = len(WORD_RE.findall(transcript.lower()))
        passed = word_count >= min_words
        return (
            100.0 if passed else 0.0,
            {
                "question_text": question_text,
                "transcript": transcript,
                "word_count": word_count,
                "min_words": min_words,
                "source": transcription.get("source"),
                "correct": passed,
            },
            {**submitted, "transcript": transcript} if isinstance(submitted, dict) else {"transcript": transcript},
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
        return target_passed




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

        tracked_lessons = [item for item in unit.lessons if item.is_active and item.type in VALID_LESSON_TYPES]
        if not tracked_lessons:
            return False, None
        rows = (
            await db.execute(
                select(UserLessonProgress).where(
                    UserLessonProgress.user_id == user.id,
                    UserLessonProgress.lesson_id.in_([item.id for item in tracked_lessons]),
                )
            )
        ).scalars().all()
        by_lesson = {item.lesson_id: item for item in rows}
        completed = all(by_lesson.get(item.id) and by_lesson[item.id].status == "completed" for item in tracked_lessons)
        scores = [by_lesson[item.id].best_score or 0 for item in tracked_lessons if by_lesson.get(item.id)]
        progress.best_score = round(sum(scores) / len(scores), 2) if scores else None
        reward = None
        if completed and progress.status != "completed":
            progress.status = "completed"
            progress.completed_at = _utcnow()
            from app.modules.gamification.services import GamificationService

            reward = await GamificationService.award_lesson_completion(db, user=user, lesson=unit)
        return completed, reward

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
    async def list_sections(
        db: AsyncSession,
        include_inactive: bool = True,
        include_units: bool = True,
        search: str | None = None,
        status: str | None = None,
        cefr_level: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> list[LearningSection]:
        stmt = select(LearningSection)
        if include_units:
            stmt = stmt.options(selectinload(LearningSection.units).selectinload(Unit.lessons))
        if not include_inactive:
            stmt = stmt.where(_truthy(LearningSection.is_active))
        if status == "active":
            stmt = stmt.where(_truthy(LearningSection.is_active))
        elif status == "inactive":
            stmt = stmt.where(~_truthy(LearningSection.is_active))
        if cefr_level:
            stmt = stmt.where(func.lower(LearningSection.cefr_level) == cefr_level.lower())
        if search:
            keyword = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(LearningSection.code).like(keyword),
                    func.lower(LearningSection.title).like(keyword),
                    func.lower(LearningSection.description).like(keyword),
                )
            )
        stmt = stmt.order_by(LearningSection.order_index.asc(), LearningSection.id.asc())
        if page is not None and page_size is not None:
            stmt = stmt.offset((max(page, 1) - 1) * page_size).limit(page_size)
        return list((await db.execute(stmt)).scalars().unique().all())

    @staticmethod
    async def count_sections(
        db: AsyncSession,
        include_inactive: bool = True,
        search: str | None = None,
        status: str | None = None,
        cefr_level: str | None = None,
    ) -> int:
        stmt = select(func.count(LearningSection.id))
        if not include_inactive:
            stmt = stmt.where(_truthy(LearningSection.is_active))
        if status == "active":
            stmt = stmt.where(_truthy(LearningSection.is_active))
        elif status == "inactive":
            stmt = stmt.where(~_truthy(LearningSection.is_active))
        if cefr_level:
            stmt = stmt.where(func.lower(LearningSection.cefr_level) == cefr_level.lower())
        if search:
            keyword = f"%{search.strip().lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(LearningSection.code).like(keyword),
                    func.lower(LearningSection.title).like(keyword),
                    func.lower(LearningSection.description).like(keyword),
                )
            )
        return int((await db.execute(stmt)).scalar_one() or 0)

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
        return await AdminCurriculumService.get_section(db, section_id)

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
        return await AdminCurriculumService.get_unit(db, unit_id)

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
        return await AdminCurriculumService.get_lesson(db, lesson_id)

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

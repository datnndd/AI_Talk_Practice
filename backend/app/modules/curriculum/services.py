from __future__ import annotations

import base64
import difflib
import os
import re
import sqlite3
import tempfile
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastapi.responses import FileResponse
from sqlalchemy import Select, String, cast, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError, UpstreamServiceError
from app.modules.curriculum.models import (
    DictionaryTerm,
    ExerciseAttempt,
    LearningLevel,
    Lesson,
    LessonExercise,
    UserExerciseProgress,
    UserLessonProgress,
)
from app.modules.curriculum.schemas import (
    DictionaryTermRead,
    ExerciseAttemptRead,
    ExerciseAttemptRequest,
    LearningLevelCreate,
    LearningLevelUpdate,
    LessonCreate,
    LessonExerciseCreate,
    LessonExerciseUpdate,
    LessonUpdate,
    ProgressSummary,
    ReorderRequest,
    StartConversationExerciseRequest,
    StartConversationExerciseResponse,
)
from app.modules.sessions.schemas.session import SessionCreate
from app.modules.sessions.services.session import SessionService
from app.modules.users.models.user import User


WORD_RE = re.compile(r"[a-z0-9']+")


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
        return base64.b64decode(_strip_data_url(value), validate=False)
    except Exception as exc:
        raise BadRequestError("Invalid audio_base64 payload") from exc


class DictionaryService:
    @staticmethod
    def audio_url_for_word(word: str) -> str:
        return f"/api/curriculum/dictionary/audio/{quote(_normalize_word(word) or word)}"

    @classmethod
    async def preview_words(cls, db: AsyncSession, words: list[str]) -> list[DictionaryTermRead]:
        return [await cls.lookup_word(db, word) for word in words]

    @classmethod
    async def lookup_word(cls, db: AsyncSession, word: str) -> DictionaryTermRead:
        normalized = _normalize_word(word)
        if not normalized:
            raise BadRequestError("Word is required")

        result = await db.execute(
            select(DictionaryTerm).where(
                DictionaryTerm.normalized_word == normalized,
                DictionaryTerm.language == "en",
            )
        )
        term = result.scalar_one_or_none()
        if term is None:
            external = cls._lookup_external_sqlite(normalized)
            term = DictionaryTerm(
                normalized_word=normalized,
                language="en",
                meaning_vi=external.get("meaning_vi"),
                ipa=external.get("ipa"),
                audio_path=external.get("audio_path"),
                source_metadata=external.get("source_metadata") or {"source": "fallback"},
            )
            db.add(term)
            await db.flush()

        return DictionaryTermRead(
            id=term.id,
            word=word,
            normalized_word=term.normalized_word,
            language=term.language,
            meaning_vi=term.meaning_vi,
            ipa=term.ipa,
            audio_url=term.audio_path or cls.audio_url_for_word(term.normalized_word),
            source_metadata=term.source_metadata or {},
        )

    @staticmethod
    def _lookup_external_sqlite(normalized_word: str) -> dict[str, Any]:
        db_path = Path(settings.dictionary_db_path or "")
        if not db_path.exists() or not db_path.is_file():
            return {}

        try:
            with sqlite3.connect(str(db_path)) as conn:
                conn.row_factory = sqlite3.Row
                tables = [row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]
                for table in tables:
                    columns = [row["name"] for row in conn.execute(f"PRAGMA table_info({table})")]
                    word_column = next((name for name in columns if name.lower() in {"word", "term", "text", "english", "en"}), None)
                    if not word_column:
                        continue
                    row = conn.execute(
                        f"SELECT * FROM {table} WHERE lower({word_column}) = ? LIMIT 1",
                        (normalized_word,),
                    ).fetchone()
                    if row is None:
                        continue
                    keys = set(row.keys())
                    meaning_key = next(
                        (
                            key
                            for key in ("meaning_vi", "vietnamese", "vi", "definition_vi", "definition", "meaning")
                            if key in keys
                        ),
                        None,
                    )
                    ipa_key = next((key for key in ("ipa", "pronunciation", "phonetic") if key in keys), None)
                    audio_key = next((key for key in ("audio_path", "audio_url", "sound") if key in keys), None)
                    return {
                        "meaning_vi": str(row[meaning_key]) if meaning_key and row[meaning_key] is not None else None,
                        "ipa": str(row[ipa_key]) if ipa_key and row[ipa_key] is not None else None,
                        "audio_path": str(row[audio_key]) if audio_key and row[audio_key] is not None else None,
                        "source_metadata": {"source": "dictionary_sqlite", "table": table},
                    }
        except Exception:
            return {}
        return {}

    @classmethod
    async def get_or_fetch_audio(cls, word: str) -> FileResponse:
        normalized = _normalize_word(word)
        if not normalized:
            raise BadRequestError("Word is required")

        cache_dir = Path(settings.dictionary_audio_cache_dir or "dictionary_audio_cache")
        cache_dir.mkdir(parents=True, exist_ok=True)
        target = cache_dir / f"{normalized.replace(' ', '_')}.mp3"
        if not target.exists():
            url = "https://translate.google.com/translate_tts"
            params = {"ie": "UTF-8", "tl": "en", "client": "tw-ob", "q": normalized}
            try:
                async with httpx.AsyncClient(timeout=15) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    target.write_bytes(response.content)
            except Exception as exc:
                raise UpstreamServiceError("Unable to fetch dictionary audio") from exc
        return FileResponse(target, media_type="audio/mpeg", filename=target.name)


class PronunciationAssessmentService:
    @classmethod
    def assess(
        cls,
        *,
        reference_text: str,
        audio_bytes: bytes | None,
        fallback_answer: Any = None,
    ) -> dict[str, Any]:
        if not audio_bytes or not settings.azure_speech_key or not settings.azure_speech_region:
            score = _score_similarity(reference_text, fallback_answer or reference_text)
            return {
                "score": score,
                "source": "local_fallback",
                "accuracy_score": score,
                "pronunciation_score": score,
                "words": [],
            }

        try:
            import azure.cognitiveservices.speech as speechsdk
        except Exception:
            score = _score_similarity(reference_text, fallback_answer or reference_text)
            return {
                "score": score,
                "source": "local_fallback_missing_sdk",
                "accuracy_score": score,
                "pronunciation_score": score,
                "words": [],
            }

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
        except Exception as exc:
            score = _score_similarity(reference_text, fallback_answer or reference_text)
            return {
                "score": score,
                "source": "local_fallback_azure_error",
                "accuracy_score": score,
                "pronunciation_score": score,
                "error": str(exc),
                "words": [],
            }
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:
                    pass


class CurriculumService:
    @staticmethod
    def _active_levels_stmt() -> Select[tuple[LearningLevel]]:
        return (
            select(LearningLevel)
            .options(selectinload(LearningLevel.lessons).selectinload(Lesson.exercises))
            .where(_truthy(LearningLevel.is_active))
            .order_by(LearningLevel.order_index.asc(), LearningLevel.id.asc())
        )

    @staticmethod
    def _flatten_lessons(levels: list[LearningLevel]) -> list[Lesson]:
        lessons: list[Lesson] = []
        for level in sorted(levels, key=lambda item: (item.order_index, item.id)):
            for lesson in sorted(level.lessons, key=lambda item: (item.order_index, item.id)):
                if lesson.is_active:
                    lessons.append(lesson)
        return lessons

    @classmethod
    async def curriculum_tree(cls, db: AsyncSession, user_id: int) -> tuple[list[LearningLevel], dict[int, UserLessonProgress], dict[int, UserExerciseProgress], set[int], int | None]:
        levels = list((await db.execute(cls._active_levels_stmt())).scalars().unique().all())
        lessons = cls._flatten_lessons(levels)
        lesson_ids = [lesson.id for lesson in lessons]
        exercise_ids = [exercise.id for lesson in lessons for exercise in lesson.exercises if exercise.is_active]

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

        exercise_progress = {}
        if exercise_ids:
            rows = (
                await db.execute(
                    select(UserExerciseProgress).where(
                        UserExerciseProgress.user_id == user_id,
                        UserExerciseProgress.exercise_id.in_(exercise_ids),
                    )
                )
            ).scalars().all()
            exercise_progress = {item.exercise_id: item for item in rows}

        completed_so_far = True
        unlocked: set[int] = set()
        current_lesson_id: int | None = None
        for lesson in lessons:
            if completed_so_far:
                unlocked.add(lesson.id)
                progress = lesson_progress.get(lesson.id)
                if current_lesson_id is None and (progress is None or progress.status != "completed"):
                    current_lesson_id = lesson.id
                completed_so_far = bool(progress and progress.status == "completed")

        return levels, lesson_progress, exercise_progress, unlocked, current_lesson_id

    @classmethod
    async def get_user_lesson(cls, db: AsyncSession, *, user_id: int, lesson_id: int) -> tuple[Lesson, dict[int, UserExerciseProgress], bool]:
        levels, _, exercise_progress, unlocked, _ = await cls.curriculum_tree(db, user_id)
        lesson = next((item for item in cls._flatten_lessons(levels) if item.id == lesson_id), None)
        if lesson is None:
            raise NotFoundError("Lesson not found")
        is_unlocked = lesson.id in unlocked
        if not is_unlocked:
            raise ForbiddenError("Complete previous lessons before opening this lesson")
        return lesson, exercise_progress, is_unlocked

    @classmethod
    async def attempt_exercise(
        cls,
        db: AsyncSession,
        *,
        user: User,
        exercise_id: int,
        payload: ExerciseAttemptRequest,
    ) -> ExerciseAttemptRead:
        exercise = await cls._get_active_exercise(db, exercise_id)
        await cls.get_user_lesson(db, user_id=user.id, lesson_id=exercise.lesson_id)

        score, feedback, answer_payload = await cls._score_exercise(db, user=user, exercise=exercise, payload=payload)
        target_passed = score >= exercise.pass_score
        attempt = ExerciseAttempt(
            user_id=user.id,
            exercise_id=exercise.id,
            answer=answer_payload,
            audio_url=payload.audio_url,
            score=score,
            passed=target_passed,
            attempt_metadata=feedback,
        )
        db.add(attempt)
        await db.flush()

        progress = await cls._get_or_create_exercise_progress(db, user.id, exercise.id)
        progress.attempt_count = (progress.attempt_count or 0) + 1
        progress.best_score = max(progress.best_score or 0, score)
        progress.state = cls._merge_progress_state(
            exercise=exercise,
            progress=progress,
            feedback=feedback,
            target_passed=target_passed,
        )
        exercise_passed = cls._exercise_is_completed(exercise=exercise, state=progress.state, target_passed=target_passed)
        progress.status = "completed" if exercise_passed else "in_progress"
        attempt.passed = exercise_passed

        lesson_completed, reward = await cls._refresh_lesson_progress(db, user=user, lesson_id=exercise.lesson_id)
        await db.commit()
        return ExerciseAttemptRead(
            id=attempt.id,
            exercise_id=exercise.id,
            score=score,
            passed=exercise_passed,
            feedback=feedback,
            progress=cls._progress_summary(progress),
            lesson_completed=lesson_completed,
            reward=reward.model_dump(mode="json") if reward else None,
        )

    @classmethod
    async def _score_exercise(
        cls,
        db: AsyncSession,
        *,
        user: User,
        exercise: LessonExercise,
        payload: ExerciseAttemptRequest,
    ) -> tuple[float, dict[str, Any], Any]:
        content = exercise.content or {}
        if exercise.type == "cloze_dictation":
            return cls._score_cloze(content, payload.answer)
        if exercise.type == "vocab_pronunciation":
            return await cls._score_vocab_pronunciation(db, content, payload)
        if exercise.type == "sentence_pronunciation":
            return cls._score_sentence_pronunciation(content, payload)
        if exercise.type == "interactive_conversation":
            return await cls._score_conversation(db, user=user, exercise=exercise, payload=payload)
        raise BadRequestError("Unsupported exercise type")

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
        db: AsyncSession,
        content: dict[str, Any],
        payload: ExerciseAttemptRequest,
    ) -> tuple[float, dict[str, Any], Any]:
        submitted = payload.answer if isinstance(payload.answer, dict) else {}
        target_word = submitted.get("word") or submitted.get("target_word")
        words = content.get("words") or []
        if not target_word and words:
            target_word = words[0].get("word") if isinstance(words[0], dict) else str(words[0])
        if not target_word:
            raise BadRequestError("Vocabulary pronunciation attempt requires a target word")

        await DictionaryService.lookup_word(db, str(target_word))
        audio_bytes = _decode_audio_base64(payload.audio_base64)
        assessment = PronunciationAssessmentService.assess(
            reference_text=str(target_word),
            audio_bytes=audio_bytes,
            fallback_answer=submitted.get("transcript") or target_word,
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
        payload: ExerciseAttemptRequest,
    ) -> tuple[float, dict[str, Any], Any]:
        reference_text = str(content.get("reference_text") or "").strip()
        if not reference_text:
            raise BadRequestError("Sentence pronunciation exercise has no reference_text")
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
        exercise: LessonExercise,
        payload: ExerciseAttemptRequest,
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
    def _merge_progress_state(
        *,
        exercise: LessonExercise,
        progress: UserExerciseProgress,
        feedback: dict[str, Any],
        target_passed: bool,
    ) -> dict[str, Any]:
        state = dict(progress.state or {})
        if exercise.type == "vocab_pronunciation":
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
                for item in (exercise.content or {}).get("words", [])
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
    def _exercise_is_completed(
        *,
        exercise: LessonExercise,
        state: dict[str, Any],
        target_passed: bool,
    ) -> bool:
        if not target_passed:
            return False
        if exercise.type != "vocab_pronunciation":
            return True
        words = [
            item.get("word") if isinstance(item, dict) else str(item)
            for item in (exercise.content or {}).get("words", [])
        ]
        passed_words = set(state.get("passed_words") or [])
        return bool(words) and all(word in passed_words for word in words)

    @classmethod
    async def start_conversation_exercise(
        cls,
        db: AsyncSession,
        *,
        user: User,
        exercise_id: int,
        payload: StartConversationExerciseRequest,
    ) -> StartConversationExerciseResponse:
        exercise = await cls._get_active_exercise(db, exercise_id)
        if exercise.type != "interactive_conversation":
            raise BadRequestError("Exercise is not an interactive conversation")
        await cls.get_user_lesson(db, user_id=user.id, lesson_id=exercise.lesson_id)
        scenario_id = int((exercise.content or {}).get("scenario_id") or 0)
        if not scenario_id:
            raise BadRequestError("Conversation exercise is missing scenario_id")

        metadata = {
            **(payload.metadata or {}),
            "curriculum_mode": True,
            "lesson_id": exercise.lesson_id,
            "exercise_id": exercise.id,
        }
        session = await SessionService.start_session(
            db,
            user_id=user.id,
            payload=SessionCreate(
                scenario_id=scenario_id,
                mode="conversation",
                metadata=metadata,
            ),
        )
        return StartConversationExerciseResponse(
            session_id=session.id,
            scenario_id=scenario_id,
            result_url=f"/sessions/{session.id}/result",
            metadata=dict(session.session_metadata or {}),
        )

    @staticmethod
    async def _get_active_exercise(db: AsyncSession, exercise_id: int) -> LessonExercise:
        exercise = (
            await db.execute(
                select(LessonExercise)
                .options(selectinload(LessonExercise.lesson).selectinload(Lesson.exercises))
                .where(LessonExercise.id == exercise_id, _truthy(LessonExercise.is_active))
            )
        ).scalar_one_or_none()
        if exercise is None:
            raise NotFoundError("Exercise not found")
        return exercise

    @staticmethod
    async def _get_or_create_exercise_progress(db: AsyncSession, user_id: int, exercise_id: int) -> UserExerciseProgress:
        progress = (
            await db.execute(
                select(UserExerciseProgress).where(
                    UserExerciseProgress.user_id == user_id,
                    UserExerciseProgress.exercise_id == exercise_id,
                )
            )
        ).scalar_one_or_none()
        if progress is None:
            progress = UserExerciseProgress(user_id=user_id, exercise_id=exercise_id, status="not_started", state={})
            db.add(progress)
            await db.flush()
        return progress

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
            progress = UserLessonProgress(user_id=user_id, lesson_id=lesson_id, status="not_started")
            db.add(progress)
            await db.flush()
        return progress

    @classmethod
    async def _refresh_lesson_progress(cls, db: AsyncSession, *, user: User, lesson_id: int) -> tuple[bool, Any | None]:
        lesson = (
            await db.execute(
                select(Lesson)
                .options(selectinload(Lesson.exercises))
                .where(Lesson.id == lesson_id)
            )
        ).scalar_one()
        progress = await cls._get_or_create_lesson_progress(db, user.id, lesson.id)
        if progress.status == "not_started":
            progress.status = "in_progress"
            progress.started_at = progress.started_at or _utcnow()

        required_exercises = [item for item in lesson.exercises if item.is_active and item.is_required]
        if not required_exercises:
            return False, None
        rows = (
            await db.execute(
                select(UserExerciseProgress).where(
                    UserExerciseProgress.user_id == user.id,
                    UserExerciseProgress.exercise_id.in_([item.id for item in required_exercises]),
                )
            )
        ).scalars().all()
        by_exercise = {item.exercise_id: item for item in rows}
        completed = all(by_exercise.get(item.id) and by_exercise[item.id].status == "completed" for item in required_exercises)
        scores = [by_exercise[item.id].best_score or 0 for item in required_exercises if by_exercise.get(item.id)]
        progress.best_score = round(sum(scores) / len(scores), 2) if scores else None
        reward = None
        if completed and progress.status != "completed":
            progress.status = "completed"
            progress.completed_at = _utcnow()
            cls._update_user_completion_counters(user, lesson, progress.best_score)
            from app.modules.gamification.services import GamificationService

            reward = await GamificationService.award_lesson_completion(db, user=user, lesson=lesson)
        return completed, reward

    @staticmethod
    def _update_user_completion_counters(user: User, lesson: Lesson, score: float | None) -> None:
        lesson_types = {exercise.type for exercise in lesson.exercises}
        if lesson_types & {"vocab_pronunciation"}:
            user.total_vocabulary_lessons_completed = (user.total_vocabulary_lessons_completed or 0) + 1
        if lesson_types & {"sentence_pronunciation", "interactive_conversation"}:
            user.total_speaking_lessons_completed = (user.total_speaking_lessons_completed or 0) + 1
        if score is not None and score >= 90:
            user.perfect_score_count = (user.perfect_score_count or 0) + 1

    @staticmethod
    def _progress_summary(progress: UserExerciseProgress | None) -> ProgressSummary:
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
    async def list_levels(db: AsyncSession, include_inactive: bool = True) -> list[LearningLevel]:
        stmt = select(LearningLevel).options(selectinload(LearningLevel.lessons).selectinload(Lesson.exercises))
        if not include_inactive:
            stmt = stmt.where(_truthy(LearningLevel.is_active))
        stmt = stmt.order_by(LearningLevel.order_index.asc(), LearningLevel.id.asc())
        return list((await db.execute(stmt)).scalars().unique().all())

    @staticmethod
    async def create_level(db: AsyncSession, body: LearningLevelCreate) -> LearningLevel:
        level = LearningLevel(**body.model_dump())
        db.add(level)
        await db.commit()
        await db.refresh(level)
        return level

    @staticmethod
    async def update_level(db: AsyncSession, level_id: int, body: LearningLevelUpdate) -> LearningLevel:
        level = await AdminCurriculumService.get_level(db, level_id)
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(level, key, value)
        await db.commit()
        await db.refresh(level)
        return level

    @staticmethod
    async def get_level(db: AsyncSession, level_id: int) -> LearningLevel:
        level = (
            await db.execute(
                select(LearningLevel)
                .options(selectinload(LearningLevel.lessons).selectinload(Lesson.exercises))
                .where(LearningLevel.id == level_id)
            )
        ).scalar_one_or_none()
        if level is None:
            raise NotFoundError("Level not found")
        return level

    @staticmethod
    async def delete_level(db: AsyncSession, level_id: int) -> LearningLevel:
        level = await AdminCurriculumService.get_level(db, level_id)
        level.is_active = False
        await db.commit()
        return level

    @staticmethod
    async def create_lesson(db: AsyncSession, body: LessonCreate) -> Lesson:
        await AdminCurriculumService.get_level(db, body.level_id)
        lesson = Lesson(**body.model_dump())
        db.add(lesson)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    @staticmethod
    async def update_lesson(db: AsyncSession, lesson_id: int, body: LessonUpdate) -> Lesson:
        lesson = await AdminCurriculumService.get_lesson(db, lesson_id)
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(lesson, key, value)
        await db.commit()
        await db.refresh(lesson)
        return lesson

    @staticmethod
    async def get_lesson(db: AsyncSession, lesson_id: int) -> Lesson:
        lesson = (
            await db.execute(
                select(Lesson)
                .options(selectinload(Lesson.exercises))
                .where(Lesson.id == lesson_id)
            )
        ).scalar_one_or_none()
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
    async def create_exercise(db: AsyncSession, body: LessonExerciseCreate) -> LessonExercise:
        await AdminCurriculumService.get_lesson(db, body.lesson_id)
        exercise = LessonExercise(**body.model_dump())
        db.add(exercise)
        await db.commit()
        await db.refresh(exercise)
        return exercise

    @staticmethod
    async def update_exercise(db: AsyncSession, exercise_id: int, body: LessonExerciseUpdate) -> LessonExercise:
        exercise = await AdminCurriculumService.get_exercise(db, exercise_id)
        for key, value in body.model_dump(exclude_unset=True).items():
            setattr(exercise, key, value)
        await db.commit()
        await db.refresh(exercise)
        return exercise

    @staticmethod
    async def get_exercise(db: AsyncSession, exercise_id: int) -> LessonExercise:
        exercise = (await db.execute(select(LessonExercise).where(LessonExercise.id == exercise_id))).scalar_one_or_none()
        if exercise is None:
            raise NotFoundError("Exercise not found")
        return exercise

    @staticmethod
    async def delete_exercise(db: AsyncSession, exercise_id: int) -> LessonExercise:
        exercise = await AdminCurriculumService.get_exercise(db, exercise_id)
        exercise.is_active = False
        await db.commit()
        return exercise

    @staticmethod
    async def reorder(db: AsyncSession, *, model: type, body: ReorderRequest) -> None:
        ids = [item.id for item in body.items]
        rows = list((await db.execute(select(model).where(model.id.in_(ids)))).scalars().all())
        by_id = {item.id: item for item in rows}
        for item in body.items:
            if item.id in by_id:
                by_id[item.id].order_index = item.order_index
        await db.commit()

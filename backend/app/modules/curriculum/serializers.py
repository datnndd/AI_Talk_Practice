from __future__ import annotations

from app.modules.curriculum.models import LearningLevel, Lesson, LessonExercise, UserExerciseProgress, UserLessonProgress
from app.modules.curriculum.schemas import LearningLevelRead, LessonExerciseRead, LessonRead, ProgressSummary


def serialize_exercise(
    exercise: LessonExercise,
    *,
    progress: UserExerciseProgress | None = None,
) -> LessonExerciseRead:
    progress_read = None
    if progress is not None:
        progress_read = ProgressSummary(
            status=progress.status,
            best_score=progress.best_score,
            attempt_count=progress.attempt_count or 0,
            state=dict(progress.state or {}),
        )
    return LessonExerciseRead.model_validate(
        {
            "id": exercise.id,
            "lesson_id": exercise.lesson_id,
            "type": exercise.type,
            "title": exercise.title,
            "order_index": exercise.order_index,
            "content": exercise.content or {},
            "pass_score": exercise.pass_score,
            "is_required": exercise.is_required,
            "is_active": exercise.is_active,
            "progress": progress_read,
            "created_at": exercise.created_at,
            "updated_at": exercise.updated_at,
        }
    )


def serialize_lesson(
    lesson: Lesson,
    *,
    lesson_progress: UserLessonProgress | None = None,
    exercise_progress: dict[int, UserExerciseProgress] | None = None,
    is_locked: bool = False,
    include_exercises: bool = True,
) -> LessonRead:
    exercises = lesson.__dict__.get("exercises", [])
    return LessonRead.model_validate(
        {
            "id": lesson.id,
            "level_id": lesson.level_id,
            "title": lesson.title,
            "description": lesson.description,
            "order_index": lesson.order_index,
            "estimated_minutes": lesson.estimated_minutes,
            "xp_reward": lesson.xp_reward,
            "coin_reward": lesson.coin_reward,
            "is_active": lesson.is_active,
            "is_locked": is_locked,
            "progress_status": lesson_progress.status if lesson_progress else "not_started",
            "best_score": lesson_progress.best_score if lesson_progress else None,
            "exercises": [
                serialize_exercise(item, progress=(exercise_progress or {}).get(item.id))
                for item in sorted(exercises, key=lambda exercise: (exercise.order_index, exercise.id))
                if include_exercises and item.is_active
            ],
            "created_at": lesson.created_at,
            "updated_at": lesson.updated_at,
        }
    )


def serialize_level(
    level: LearningLevel,
    *,
    lesson_progress: dict[int, UserLessonProgress] | None = None,
    exercise_progress: dict[int, UserExerciseProgress] | None = None,
    unlocked_lesson_ids: set[int] | None = None,
    include_exercises: bool = False,
) -> LearningLevelRead:
    unlocked_lesson_ids = unlocked_lesson_ids or set()
    lessons = level.__dict__.get("lessons", [])
    return LearningLevelRead.model_validate(
        {
            "id": level.id,
            "code": level.code,
            "title": level.title,
            "description": level.description,
            "order_index": level.order_index,
            "is_active": level.is_active,
            "lessons": [
                serialize_lesson(
                    lesson,
                    lesson_progress=(lesson_progress or {}).get(lesson.id),
                    exercise_progress=exercise_progress or {},
                    is_locked=lesson.id not in unlocked_lesson_ids,
                    include_exercises=include_exercises,
                )
                for lesson in sorted(lessons, key=lambda item: (item.order_index, item.id))
                if lesson.is_active
            ],
            "created_at": level.created_at,
            "updated_at": level.updated_at,
        }
    )

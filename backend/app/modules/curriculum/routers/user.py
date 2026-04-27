from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.curriculum.serializers import serialize_level, serialize_lesson
from app.modules.curriculum.schemas import (
    CurriculumTreeRead,
    ExerciseAttemptRead,
    ExerciseAttemptRequest,
    LessonRead,
    StartConversationExerciseRequest,
    StartConversationExerciseResponse,
)
from app.modules.curriculum.services import CurriculumService, DictionaryService
from app.modules.users.models.user import User

router = APIRouter(tags=["curriculum"])


@router.get("/curriculum", response_model=CurriculumTreeRead)
async def get_curriculum(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    levels, lesson_progress, exercise_progress, unlocked, current_lesson_id = await CurriculumService.curriculum_tree(
        db,
        user.id,
    )
    return CurriculumTreeRead(
        levels=[
            serialize_level(
                level,
                lesson_progress=lesson_progress,
                exercise_progress=exercise_progress,
                unlocked_lesson_ids=unlocked,
            )
            for level in levels
        ],
        current_lesson_id=current_lesson_id,
    )


@router.get("/lessons/{lesson_id}", response_model=LessonRead)
async def get_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    lesson, exercise_progress, _ = await CurriculumService.get_user_lesson(db, user_id=user.id, lesson_id=lesson_id)
    _, lesson_progress, _, unlocked, _ = await CurriculumService.curriculum_tree(db, user.id)
    return serialize_lesson(
        lesson,
        lesson_progress=lesson_progress.get(lesson.id),
        exercise_progress=exercise_progress,
        is_locked=lesson.id not in unlocked,
        include_exercises=True,
    )


@router.post("/exercises/{exercise_id}/attempt", response_model=ExerciseAttemptRead, status_code=status.HTTP_201_CREATED)
async def attempt_exercise(
    exercise_id: int,
    body: ExerciseAttemptRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CurriculumService.attempt_exercise(db, user=user, exercise_id=exercise_id, payload=body)


@router.post("/exercises/{exercise_id}/start-conversation", response_model=StartConversationExerciseResponse)
async def start_conversation_exercise(
    exercise_id: int,
    body: StartConversationExerciseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CurriculumService.start_conversation_exercise(db, user=user, exercise_id=exercise_id, payload=body)


@router.get("/curriculum/dictionary/audio/{word}")
async def dictionary_audio(word: str):
    return await DictionaryService.get_or_fetch_audio(word)

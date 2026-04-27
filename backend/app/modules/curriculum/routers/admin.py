from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.curriculum.models import LearningLevel, Lesson, LessonExercise
from app.modules.curriculum.serializers import serialize_exercise, serialize_level, serialize_lesson
from app.modules.curriculum.schemas import (
    DictionaryPreviewRequest,
    DictionaryTermRead,
    LearningLevelCreate,
    LearningLevelRead,
    LearningLevelUpdate,
    LessonCreate,
    LessonExerciseCreate,
    LessonExerciseRead,
    LessonExerciseUpdate,
    LessonRead,
    LessonUpdate,
    ReorderRequest,
)
from app.modules.curriculum.services import AdminCurriculumService, DictionaryService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/curriculum", tags=["admin-curriculum"])


@router.get("/levels", response_model=list[LearningLevelRead])
async def list_levels(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    levels = await AdminCurriculumService.list_levels(db, include_inactive=True)
    return [
        serialize_level(
            level,
            unlocked_lesson_ids={lesson.id for lesson in level.lessons},
            include_exercises=True,
        )
        for level in levels
    ]


@router.post("/levels", response_model=LearningLevelRead, status_code=status.HTTP_201_CREATED)
async def create_level(
    body: LearningLevelCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    level = await AdminCurriculumService.create_level(db, body)
    return serialize_level(level, unlocked_lesson_ids=set())


@router.put("/levels/{level_id}", response_model=LearningLevelRead)
async def update_level(
    level_id: int,
    body: LearningLevelUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    level = await AdminCurriculumService.update_level(db, level_id, body)
    return serialize_level(level, unlocked_lesson_ids={lesson.id for lesson in level.lessons}, include_exercises=True)


@router.delete("/levels/{level_id}", response_model=LearningLevelRead)
async def delete_level(
    level_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    level = await AdminCurriculumService.delete_level(db, level_id)
    return serialize_level(level, unlocked_lesson_ids={lesson.id for lesson in level.lessons}, include_exercises=True)


@router.post("/levels/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_levels(
    body: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    await AdminCurriculumService.reorder(db, model=LearningLevel, body=body)


@router.post("/lessons", response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    body: LessonCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    lesson = await AdminCurriculumService.create_lesson(db, body)
    return serialize_lesson(lesson, is_locked=False)


@router.put("/lessons/{lesson_id}", response_model=LessonRead)
async def update_lesson(
    lesson_id: int,
    body: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    lesson = await AdminCurriculumService.update_lesson(db, lesson_id, body)
    return serialize_lesson(lesson, is_locked=False)


@router.delete("/lessons/{lesson_id}", response_model=LessonRead)
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    lesson = await AdminCurriculumService.delete_lesson(db, lesson_id)
    return serialize_lesson(lesson, is_locked=False)


@router.post("/lessons/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_lessons(
    body: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    await AdminCurriculumService.reorder(db, model=Lesson, body=body)


@router.post("/exercises", response_model=LessonExerciseRead, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    body: LessonExerciseCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    exercise = await AdminCurriculumService.create_exercise(db, body)
    return serialize_exercise(exercise)


@router.put("/exercises/{exercise_id}", response_model=LessonExerciseRead)
async def update_exercise(
    exercise_id: int,
    body: LessonExerciseUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    exercise = await AdminCurriculumService.update_exercise(db, exercise_id, body)
    return serialize_exercise(exercise)


@router.delete("/exercises/{exercise_id}", response_model=LessonExerciseRead)
async def delete_exercise(
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    exercise = await AdminCurriculumService.delete_exercise(db, exercise_id)
    return serialize_exercise(exercise)


@router.post("/exercises/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_exercises(
    body: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    await AdminCurriculumService.reorder(db, model=LessonExercise, body=body)


@router.post("/dictionary/preview", response_model=list[DictionaryTermRead])
async def preview_dictionary_words(
    body: DictionaryPreviewRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await DictionaryService.preview_words(db, body.words)

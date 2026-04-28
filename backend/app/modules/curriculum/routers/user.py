from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.curriculum.serializers import serialize_section, serialize_unit
from app.modules.curriculum.schemas import (
    CurriculumTreeRead,
    LessonAttemptRead,
    LessonAttemptRequest,
    StartConversationLessonRequest,
    StartConversationLessonResponse,
    UnitRead,
)
from app.modules.curriculum.services import CurriculumService, DictionaryApiService
from app.modules.users.models.user import User

router = APIRouter(tags=["curriculum"])


@router.get("/curriculum", response_model=CurriculumTreeRead)
async def get_curriculum(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sections, unit_progress, lesson_progress, unlocked, current_unit_id = await CurriculumService.curriculum_tree(
        db,
        user.id,
    )
    return CurriculumTreeRead(
        sections=[
            serialize_section(
                section,
                unit_progress=unit_progress,
                lesson_progress=lesson_progress,
                unlocked_unit_ids=unlocked,
            )
            for section in sections
        ],
        current_unit_id=current_unit_id,
    )


@router.get("/units/{unit_id}", response_model=UnitRead)
async def get_unit(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    unit, lesson_progress, is_unlocked, unit_progress = await CurriculumService.get_user_unit(
        db,
        user_id=user.id,
        unit_id=unit_id,
    )
    return serialize_unit(
        unit,
        unit_progress=unit_progress,
        lesson_progress=lesson_progress,
        is_locked=not is_unlocked,
        include_lessons=True,
    )


@router.post("/lessons/{lesson_id}/attempt", response_model=LessonAttemptRead, status_code=status.HTTP_201_CREATED)
async def attempt_lesson(
    lesson_id: int,
    body: LessonAttemptRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CurriculumService.attempt_lesson(db, user=user, lesson_id=lesson_id, payload=body)


@router.post("/lessons/{lesson_id}/start-conversation", response_model=StartConversationLessonResponse)
async def start_conversation_lesson(
    lesson_id: int,
    body: StartConversationLessonRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await CurriculumService.start_conversation_lesson(db, user=user, lesson_id=lesson_id, payload=body)


@router.get("/curriculum/dictionary/audio")
async def dictionary_audio(
    word: str = Query(min_length=1),
    lang: str = Query(default="en", min_length=2, max_length=10),
    db: AsyncSession = Depends(get_db),
):
    return await DictionaryApiService.get_audio_response(db, word=word, language=lang)

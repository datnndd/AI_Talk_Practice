from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.curriculum.serializers import serialize_section, serialize_unit
from app.modules.curriculum.schemas import (
    CurriculumTreeRead,
    LessonAttemptRead,
    LessonAttemptRequest,
    UnitRead,
)
from app.modules.curriculum.services import CurriculumService
from app.modules.curriculum.services import _normalize_cefr_level
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
        user_cefr=user.current_cefr or user.level,
    )
    return CurriculumTreeRead(
        sections=[
            serialize_section(
                section,
                unit_progress=unit_progress,
                lesson_progress=lesson_progress,
                unlocked_unit_ids=unlocked,
                include_units=False,
            )
            for section in sections
        ],
        current_unit_id=current_unit_id,
        current_cefr=_normalize_cefr_level(user.current_cefr or user.level),
    )


@router.get("/curriculum/sections/{section_id}", response_model=CurriculumTreeRead)
async def get_curriculum_section(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sections, unit_progress, lesson_progress, unlocked, current_unit_id = await CurriculumService.curriculum_tree(
        db,
        user.id,
        user_cefr=user.current_cefr or user.level,
        include_lesson_progress=True,
    )
    section = next((item for item in sections if item.id == section_id), None)
    if section is None:
        from app.core.exceptions import NotFoundError

        raise NotFoundError("Section not found")
    return CurriculumTreeRead(
        sections=[
            serialize_section(
                section,
                unit_progress=unit_progress,
                lesson_progress=lesson_progress,
                unlocked_unit_ids=unlocked,
                include_lessons=False,
            )
        ],
        current_unit_id=current_unit_id,
        current_cefr=_normalize_cefr_level(user.current_cefr or user.level),
    )


@router.get("/units/{unit_id}", response_model=UnitRead)
async def get_unit(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    unit, lesson_progress, is_unlocked, unit_progress = await CurriculumService.get_user_unit(
        db,
        user=user,
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

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.curriculum.models import Lesson
from app.modules.curriculum.serializers import serialize_lesson, serialize_section, serialize_unit
from app.modules.curriculum.schemas import (
    LearningSectionCreate,
    LearningSectionListResponse,
    LearningSectionRead,
    LearningSectionUpdate,
    LessonCreate,
    LessonAudioAssetRead,
    LessonAudioTTSRequest,
    LessonRead,
    LessonUpdate,
    ReorderRequest,
    UnitCreate,
    UnitRead,
    UnitUpdate,
)
from app.modules.curriculum.services import AdminCurriculumService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/curriculum", tags=["admin-curriculum"])


@router.post("/audio/tts", response_model=LessonAudioAssetRead, status_code=status.HTTP_201_CREATED)
async def create_lesson_tts_audio(
    body: LessonAudioTTSRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminCurriculumService.create_tts_audio(db, body)


@router.post("/audio/upload", response_model=LessonAudioAssetRead, status_code=status.HTTP_201_CREATED)
async def upload_lesson_audio(
    file: UploadFile = File(...),
    lesson_id: int | None = Form(default=None),
    text: str | None = Form(default=None),
    language: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    audio_bytes = await file.read()
    return await AdminCurriculumService.upload_audio(
        db,
        audio_bytes=audio_bytes,
        filename=file.filename,
        content_type=file.content_type,
        lesson_id=lesson_id,
        text=text,
        language=language,
    )


@router.get("/sections/summary-paged", response_model=LearningSectionListResponse)
async def list_section_summaries_paged(
    search: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    cefr_level: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=30, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    sections = await AdminCurriculumService.list_sections(
        db,
        include_inactive=True,
        include_units=False,
        search=search,
        status=status_filter,
        cefr_level=cefr_level,
        page=page,
        page_size=page_size,
    )
    total = await AdminCurriculumService.count_sections(
        db,
        include_inactive=True,
        search=search,
        status=status_filter,
        cefr_level=cefr_level,
    )
    return LearningSectionListResponse(
        items=[serialize_section(section, unlocked_unit_ids=set(), include_lessons=False, include_inactive=True) for section in sections],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/sections/{section_id}", response_model=LearningSectionRead)
async def get_section(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    section = await AdminCurriculumService.get_section(db, section_id)
    return serialize_section(
        section,
        unlocked_unit_ids={unit.id for unit in section.units},
        include_lessons=True,
        include_inactive=True,
        include_lesson_content=False,
    )


@router.post("/sections", response_model=LearningSectionRead, status_code=status.HTTP_201_CREATED)
async def create_section(
    body: LearningSectionCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    section = await AdminCurriculumService.create_section(db, body)
    return serialize_section(section, unlocked_unit_ids=set())


@router.put("/sections/{section_id}", response_model=LearningSectionRead)
async def update_section(
    section_id: int,
    body: LearningSectionUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    section = await AdminCurriculumService.update_section(db, section_id, body)
    return serialize_section(
        section,
        unlocked_unit_ids={unit.id for unit in section.units},
        include_lessons=True,
        include_inactive=True,
    )


@router.delete("/sections/{section_id}", response_model=LearningSectionRead)
async def delete_section(
    section_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    section = await AdminCurriculumService.delete_section(db, section_id)
    return serialize_section(
        section,
        unlocked_unit_ids={unit.id for unit in section.units},
        include_lessons=True,
        include_inactive=True,
    )


@router.post("/units", response_model=UnitRead, status_code=status.HTTP_201_CREATED)
async def create_unit(
    body: UnitCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    unit = await AdminCurriculumService.create_unit(db, body)
    return serialize_unit(unit, is_locked=False)


@router.put("/units/{unit_id}", response_model=UnitRead)
async def update_unit(
    unit_id: int,
    body: UnitUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    unit = await AdminCurriculumService.update_unit(db, unit_id, body)
    return serialize_unit(unit, is_locked=False)


@router.delete("/units/{unit_id}", response_model=UnitRead)
async def delete_unit(
    unit_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    unit = await AdminCurriculumService.delete_unit(db, unit_id)
    return serialize_unit(unit, is_locked=False)


@router.post("/lessons", response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    body: LessonCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    lesson = await AdminCurriculumService.create_lesson(db, body)
    return serialize_lesson(lesson)


@router.get("/lessons/{lesson_id}", response_model=LessonRead)
async def get_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    lesson = await AdminCurriculumService.get_lesson(db, lesson_id)
    return serialize_lesson(lesson)


@router.put("/lessons/{lesson_id}", response_model=LessonRead)
async def update_lesson(
    lesson_id: int,
    body: LessonUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    lesson = await AdminCurriculumService.update_lesson(db, lesson_id, body)
    return serialize_lesson(lesson)


@router.delete("/lessons/{lesson_id}", response_model=LessonRead)
async def delete_lesson(
    lesson_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    lesson = await AdminCurriculumService.delete_lesson(db, lesson_id)
    return serialize_lesson(lesson)


@router.post("/lessons/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_lessons(
    body: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    await AdminCurriculumService.reorder(db, model=Lesson, body=body)

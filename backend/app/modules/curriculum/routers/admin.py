from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.curriculum.models import LearningSection, Lesson, Unit
from app.modules.curriculum.serializers import serialize_lesson, serialize_section, serialize_unit
from app.modules.curriculum.schemas import (
    DictionaryLookupRead,
    LearningSectionCreate,
    LearningSectionRead,
    LearningSectionUpdate,
    LessonCreate,
    LessonRead,
    LessonUpdate,
    ReorderRequest,
    UnitCreate,
    UnitRead,
    UnitUpdate,
)
from app.modules.curriculum.services import AdminCurriculumService, DictionaryApiService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/curriculum", tags=["admin-curriculum"])


@router.get("/dictionary/lookup", response_model=DictionaryLookupRead)
async def dictionary_lookup(
    word: str,
    lang: str = "en",
    def_lang: str = "vi",
    _: User = Depends(require_admin_user),
):
    return await DictionaryApiService.lookup_word(word=word, language=lang, definition_language=def_lang)


@router.get("/sections", response_model=list[LearningSectionRead])
async def list_sections(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    sections = await AdminCurriculumService.list_sections(db, include_inactive=True)
    return [
        serialize_section(
            section,
            unlocked_unit_ids={unit.id for unit in section.units},
            include_lessons=True,
            include_inactive=True,
            include_lesson_content=False,
        )
        for section in sections
    ]


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


@router.post("/sections/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_sections(
    body: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    await AdminCurriculumService.reorder(db, model=LearningSection, body=body)


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


@router.post("/units/reorder", status_code=status.HTTP_204_NO_CONTENT)
async def reorder_units(
    body: ReorderRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    await AdminCurriculumService.reorder(db, model=Unit, body=body)


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

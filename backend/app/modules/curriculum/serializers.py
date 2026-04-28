from __future__ import annotations

from urllib.parse import urlencode

from app.modules.curriculum.models import LearningSection, Lesson, Unit, UserLessonProgress, UserUnitProgress
from app.modules.curriculum.schemas import LearningSectionRead, LessonRead, ProgressSummary, UnitRead


def dictionary_audio_url(word: str, language: str = "en") -> str:
    query = urlencode({"word": word, "lang": language or "en"})
    return f"/api/curriculum/dictionary/audio?{query}"


def _enriched_lesson_content(lesson: Lesson) -> dict:
    content = dict(lesson.content or {})
    if lesson.type != "word_audio_choice":
        return content

    language = content.get("language") or "en"
    enriched_options = []
    for option in content.get("options") or []:
        if not isinstance(option, dict):
            continue
        word = str(option.get("word") or "").strip()
        enriched_options.append(
            {
                **option,
                "audio_url": dictionary_audio_url(word, language) if word else None,
                "source": "dict.minhqnd.com",
            }
        )
    content["language"] = language
    content["options"] = enriched_options
    return content


def serialize_lesson(
    lesson: Lesson,
    *,
    progress: UserLessonProgress | None = None,
    include_content: bool = True,
) -> LessonRead:
    progress_read = None
    if progress is not None:
        progress_read = ProgressSummary(
            status=progress.status,
            best_score=progress.best_score,
            attempt_count=progress.attempt_count or 0,
            state=dict(progress.state or {}),
        )
    return LessonRead.model_validate(
        {
            "id": lesson.id,
            "unit_id": lesson.unit_id,
            "type": lesson.type,
            "title": lesson.title,
            "order_index": lesson.order_index,
            "content": _enriched_lesson_content(lesson) if include_content else {},
            "pass_score": lesson.pass_score,
            "is_required": lesson.is_required,
            "is_active": lesson.is_active,
            "progress": progress_read,
            "created_at": lesson.created_at,
            "updated_at": lesson.updated_at,
        }
    )


def serialize_unit(
    unit: Unit,
    *,
    unit_progress: UserUnitProgress | None = None,
    lesson_progress: dict[int, UserLessonProgress] | None = None,
    is_locked: bool = False,
    include_lessons: bool = True,
    include_inactive: bool = False,
    include_lesson_content: bool = True,
) -> UnitRead:
    lessons = unit.__dict__.get("lessons", [])
    return UnitRead.model_validate(
        {
            "id": unit.id,
            "section_id": unit.section_id,
            "title": unit.title,
            "description": unit.description,
            "order_index": unit.order_index,
            "estimated_minutes": unit.estimated_minutes,
            "xp_reward": unit.xp_reward,
            "coin_reward": unit.coin_reward,
            "is_active": unit.is_active,
            "is_locked": is_locked,
            "progress_status": unit_progress.status if unit_progress else "not_started",
            "best_score": unit_progress.best_score if unit_progress else None,
            "lessons": [
                serialize_lesson(
                    item,
                    progress=(lesson_progress or {}).get(item.id),
                    include_content=include_lesson_content,
                )
                for item in sorted(lessons, key=lambda lesson: (lesson.order_index, lesson.id))
                if include_lessons and (include_inactive or item.is_active)
            ],
            "created_at": unit.created_at,
            "updated_at": unit.updated_at,
        }
    )


def serialize_section(
    section: LearningSection,
    *,
    unit_progress: dict[int, UserUnitProgress] | None = None,
    lesson_progress: dict[int, UserLessonProgress] | None = None,
    unlocked_unit_ids: set[int] | None = None,
    include_lessons: bool = False,
    include_inactive: bool = False,
    include_lesson_content: bool = True,
) -> LearningSectionRead:
    unlocked_unit_ids = unlocked_unit_ids or set()
    units = section.__dict__.get("units", [])
    return LearningSectionRead.model_validate(
        {
            "id": section.id,
            "code": section.code,
            "title": section.title,
            "cefr_level": section.cefr_level,
            "description": section.description,
            "order_index": section.order_index,
            "is_active": section.is_active,
            "units": [
                serialize_unit(
                    unit,
                    unit_progress=(unit_progress or {}).get(unit.id),
                    lesson_progress=lesson_progress or {},
                    is_locked=unit.id not in unlocked_unit_ids,
                    include_lessons=include_lessons,
                    include_inactive=include_inactive,
                    include_lesson_content=include_lesson_content,
                )
                for unit in sorted(units, key=lambda item: (item.order_index, item.id))
                if include_inactive or unit.is_active
            ],
            "created_at": section.created_at,
            "updated_at": section.updated_at,
        }
    )

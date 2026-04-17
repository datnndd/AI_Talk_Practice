"""Lesson-oriented conversation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.config import settings
from app.core.exceptions import BadRequestError
from app.infra.factory import create_llm
from app.modules.sessions.schemas.lesson import (
    LessonGenerateRequest,
    LessonHintRead,
    LessonHintRequest,
    LessonNextQuestionRequest,
    LessonStateRead,
)
from app.modules.sessions.services.lesson_runtime import LessonRuntimeService
from app.modules.sessions.services.session import SessionService
from app.modules.users.models.user import User

router = APIRouter(prefix="/lessons", tags=["lessons"])


def _lesson_metadata(package, state, hints):
    return {"lesson": LessonRuntimeService.serialize_lesson_metadata(package=package, state=state, hints=hints)}


@router.post("/generate", response_model=LessonStateRead, status_code=status.HTTP_201_CREATED)
async def generate_lesson(
    body: LessonGenerateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await SessionService.get_by_id(db, body.session_id, user.id)
    if session.scenario_id != body.scenario_id:
        raise BadRequestError("Scenario does not match the selected session")

    planning_llm = None
    try:
        planning_llm = create_llm(settings)
        package, state, hints = await LessonRuntimeService.ensure_session_lesson_dynamic(
            scenario=session.scenario,
            session_metadata=session.session_metadata,
            level=body.level or user.level,
            llm=planning_llm,
            regenerate=body.regenerate,
        )
    except Exception:
        package, state, hints = LessonRuntimeService.ensure_session_lesson(
            scenario=session.scenario,
            session_metadata=session.session_metadata,
            level=body.level or user.level,
            regenerate=body.regenerate,
        )
    finally:
        if planning_llm is not None:
            await planning_llm.close()
    await SessionService.merge_session_metadata(
        db,
        session_id=session.id,
        user_id=user.id,
        metadata=_lesson_metadata(package, state, hints),
    )
    return LessonRuntimeService.build_state_read(
        session_id=session.id,
        scenario=session.scenario,
        package=package,
        state=state,
    )


@router.post("/next-question", response_model=LessonStateRead)
async def next_question(
    body: LessonNextQuestionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await SessionService.get_by_id(db, body.session_id, user.id)
    if not LessonRuntimeService.has_lesson(session.session_metadata):
        raise BadRequestError("Lesson has not been generated for this session")

    package, state, hints = LessonRuntimeService.deserialize_lesson_metadata(session.session_metadata)
    if package.lesson_id != body.lesson_id:
        raise BadRequestError("Lesson id does not match the active session lesson")

    result = LessonRuntimeService.advance(
        scenario=session.scenario,
        session_id=session.id,
        package=package,
        state=state,
        user_answer=body.user_answer,
    )
    await SessionService.merge_session_metadata(
        db,
        session_id=session.id,
        user_id=user.id,
        metadata=_lesson_metadata(package, state, hints),
    )
    return result.state


@router.post("/hint", response_model=LessonHintRead)
async def build_hint(
    body: LessonHintRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await SessionService.get_by_id(db, body.session_id, user.id)
    if not LessonRuntimeService.has_lesson(session.session_metadata):
        raise BadRequestError("Lesson has not been generated for this session")

    package, state, hints = LessonRuntimeService.deserialize_lesson_metadata(session.session_metadata)
    if package.lesson_id != body.lesson_id:
        raise BadRequestError("Lesson id does not match the active session lesson")

    current_objective_id = body.objective_id or package.objectives[state.current_objective_index].objective_id
    current_objective = package.objectives[state.current_objective_index]
    current_question = (state.last_question or current_objective.main_question or "").strip()
    follow_up_index = state.follow_up_index_by_objective.get(current_objective_id, 0)
    cached = LessonRuntimeService.get_cached_hint(
        hints=hints,
        objective_id=current_objective_id,
        question=current_question,
        follow_up_index=follow_up_index,
    )
    if cached:
        return cached.model_copy(update={"cached": True})

    hint_llm = None
    try:
        hint_llm = create_llm(settings)
        payload = await LessonRuntimeService.build_hint_dynamic(
            scenario=session.scenario,
            package=package,
            state=state,
            llm=hint_llm,
        )
    except Exception:
        payload = LessonRuntimeService.build_hint(
            package=package,
            state=state,
            user_last_answer=body.user_last_answer,
        )
    finally:
        if hint_llm is not None:
            await hint_llm.close()

    updated_hints = LessonRuntimeService.store_hint(
        hints=hints,
        objective_id=current_objective_id,
        question=current_question,
        payload=payload,
        follow_up_index=follow_up_index,
    )
    await SessionService.merge_session_metadata(
        db,
        session_id=session.id,
        user_id=user.id,
        metadata=_lesson_metadata(package, state, updated_hints),
    )
    return payload

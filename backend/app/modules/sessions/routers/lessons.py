"""Lesson-oriented conversation endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.core.exceptions import BadRequestError
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

    package, state, hints = LessonRuntimeService.ensure_session_lesson(
        scenario=session.scenario,
        session_metadata=session.session_metadata,
        level=body.level or user.level,
        regenerate=body.regenerate,
    )
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
    cached = LessonRuntimeService.get_cached_hint(
        hints=hints,
        objective_id=current_objective_id,
        answer=body.user_last_answer,
    )
    if cached:
        return cached.model_copy(update={"cached": True})

    payload = LessonRuntimeService.build_hint(
        package=package,
        state=state,
        user_last_answer=body.user_last_answer,
    )
    updated_hints = LessonRuntimeService.store_hint(
        hints=hints,
        objective_id=current_objective_id,
        answer=body.user_last_answer,
        payload=payload,
    )
    await SessionService.merge_session_metadata(
        db,
        session_id=session.id,
        user_id=user.id,
        metadata=_lesson_metadata(package, state, updated_hints),
    )
    return payload

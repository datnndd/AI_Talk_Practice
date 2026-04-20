"""Session lifecycle and message endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.users.models.user import User
from app.modules.sessions.serializers import (
    serialize_message,
    serialize_session,
    serialize_session_list_item,
)
from app.modules.sessions.schemas.session import (
    MessageCreate,
    MessageRead,
    RealtimeCorrectionRequest,
    RealtimeCorrectionResponse,
    SessionCreate,
    SessionFinishRequest,
    SessionHintRequest,
    SessionListItem,
    SessionRead,
)
from app.modules.sessions.schemas.lesson import LessonHintRead
from app.modules.sessions.services.session import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("", response_model=SessionRead, status_code=status.HTTP_201_CREATED)
async def start_session(
    body: SessionCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await SessionService.start_session(db, user_id=user.id, payload=body)
    return serialize_session(session)


@router.get("", response_model=list[SessionListItem])
async def list_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sessions = await SessionService.list_for_user(db, user.id, limit, offset)
    return [serialize_session_list_item(item) for item in sessions]


@router.get("/{session_id}", response_model=SessionRead)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await SessionService.get_by_id(db, session_id, user.id)
    return serialize_session(session)


@router.post("/{session_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def add_message(
    session_id: int,
    body: MessageCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    message = await SessionService.add_message(db, session_id=session_id, user_id=user.id, payload=body)
    return serialize_message(message)


@router.post("/{session_id}/hint", response_model=LessonHintRead)
async def build_session_hint(
    session_id: int,
    body: SessionHintRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await SessionService.build_hint(
        db,
        session_id=session_id,
        user_id=user.id,
        payload=body,
        user_level=user.level,
    )


@router.post("/{session_id}/corrections", response_model=RealtimeCorrectionResponse)
async def correct_session_message(
    session_id: int,
    body: RealtimeCorrectionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await SessionService.correct_realtime(db, session_id=session_id, user_id=user.id, payload=body)


@router.post("/{session_id}/end", response_model=SessionRead)
async def end_session(
    session_id: int,
    body: SessionFinishRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    session = await SessionService.end_session(db, session_id=session_id, user_id=user.id, payload=body)
    return serialize_session(session)

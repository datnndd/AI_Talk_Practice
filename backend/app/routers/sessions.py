"""
Session history router — list & detail.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth import get_current_user
from app.schemas import SessionListItem, SessionDetailResponse, MessageResponse, SessionScoreResponse
from app.models.user import User
from app.models.session import Session

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


@router.get("", response_model=List[SessionListItem])
async def list_sessions(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """List user's conversation sessions, newest first."""
    q = (
        select(Session)
        .where(Session.user_id == user.id)
        .order_by(Session.started_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(q)
    sessions = result.scalars().all()

    items = []
    for s in sessions:
        items.append(SessionListItem(
            id=s.id,
            scenario_title=s.scenario.title if s.scenario else "Unknown",
            status=s.status,
            duration_seconds=s.duration_seconds,
            started_at=s.started_at,
            ended_at=s.ended_at,
            overall_score=s.score.overall_score if s.score else None,
        ))
    return items


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get full session detail with messages, corrections, and scores."""
    result = await db.execute(
        select(Session).where(Session.id == session_id, Session.user_id == user.id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDetailResponse(
        id=session.id,
        scenario_id=session.scenario_id,
        scenario_title=session.scenario.title if session.scenario else "Unknown",
        status=session.status,
        duration_seconds=session.duration_seconds,
        started_at=session.started_at,
        ended_at=session.ended_at,
        messages=[MessageResponse.model_validate(m) for m in session.messages],
        score=SessionScoreResponse.model_validate(session.score) if session.score else None,
    )

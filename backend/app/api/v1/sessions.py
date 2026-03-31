"""
Session history router — list & detail.
"""

from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.session import SessionListItem, SessionDetailResponse, MessageResponse, SessionScoreResponse
from app.services.session_service import SessionService

router = APIRouter(prefix="/sessions", tags=["sessions"])

@router.get("", response_model=List[SessionListItem])
async def list_sessions(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    sessions = await SessionService.list_for_user(db, user.id, limit, offset)
    
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
    session = await SessionService.get_by_id(db, session_id, user.id)
    
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

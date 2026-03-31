from typing import List

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.session import Session

class SessionService:
    @staticmethod
    async def list_for_user(db: AsyncSession, user_id: int, limit: int = 20, offset: int = 0) -> List[Session]:
        q = (
            select(Session)
            .options(selectinload(Session.scenario), selectinload(Session.score))
            .where(Session.user_id == user_id)
            .order_by(Session.started_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: int, user_id: int) -> Session:
        result = await db.execute(
            select(Session)
            .options(selectinload(Session.scenario), selectinload(Session.score), selectinload(Session.messages))
            .where(Session.id == session_id, Session.user_id == user_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session

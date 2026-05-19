from __future__ import annotations

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.message_realtime_feedback import MessageRealtimeFeedback
from app.modules.sessions.models.session import Session
from app.modules.sessions.models.session_score import SessionScore


FULL_SESSION_LOAD = (
    joinedload(Session.scenario).joinedload(Scenario.character),
    joinedload(Session.character),
    joinedload(Session.score),
    selectinload(Session.messages).selectinload(Message.realtime_feedback),
)


class SessionRepository:
    @staticmethod
    async def create_session(db: AsyncSession, **values: object) -> Session:
        session = Session(**values)
        db.add(session)
        await db.flush()
        return session

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        user_id: int,
        *,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Session]:
        stmt = (
            select(Session)
            .options(joinedload(Session.scenario).joinedload(Scenario.character), joinedload(Session.character), joinedload(Session.score))
            .where(Session.user_id == user_id, Session.deleted_at.is_(None))
            .order_by(Session.started_at.desc(), Session.id.desc())
            .limit(limit)
            .offset(offset)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_by_id_for_user(
        db: AsyncSession,
        session_id: int,
        user_id: int,
        *,
        full: bool = True,
    ) -> Session | None:
        stmt = select(Session).where(
            Session.id == session_id,
            Session.user_id == user_id,
            Session.deleted_at.is_(None),
        )
        if full:
            stmt = stmt.options(*FULL_SESSION_LOAD)
        else:
            stmt = stmt.options(joinedload(Session.scenario).joinedload(Scenario.character), joinedload(Session.character), joinedload(Session.score))
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_by_id(
        db: AsyncSession,
        session_id: int,
        *,
        full: bool = True,
    ) -> Session | None:
        stmt = select(Session).where(Session.id == session_id, Session.deleted_at.is_(None))
        if full:
            stmt = stmt.options(*FULL_SESSION_LOAD)
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def get_latest_objective_completed_for_user_scenario(
        db: AsyncSession,
        *,
        user_id: int,
        scenario_id: int,
    ) -> Session | None:
        objective_completion = SessionScore.score_metadata["objective_completion"].as_string()
        stmt = (
            select(Session)
            .join(SessionScore, SessionScore.session_id == Session.id)
            .options(joinedload(Session.score))
            .where(
                Session.user_id == user_id,
                Session.scenario_id == scenario_id,
                Session.status == "completed",
                Session.deleted_at.is_(None),
                objective_completion == "completed",
            )
            .order_by(
                desc(Session.ended_at).nulls_last(),
                desc(Session.started_at),
                desc(Session.id),
            )
            .limit(1)
        )
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def count_messages(db: AsyncSession, session_id: int, *, role: str | None = None) -> int:
        stmt = select(func.count(Message.id)).where(Message.session_id == session_id)
        if role is not None:
            stmt = stmt.where(Message.role == role)
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)

    @staticmethod
    async def get_message_for_session(
        db: AsyncSession,
        *,
        session_id: int,
        message_id: int,
    ) -> Message | None:
        stmt = (
            select(Message)
            .options(selectinload(Message.realtime_feedback))
            .where(Message.id == message_id, Message.session_id == session_id)
        )
        result = await db.execute(stmt)
        return result.unique().scalar_one_or_none()

    @staticmethod
    async def next_order_index(db: AsyncSession, session_id: int) -> int:
        stmt = select(func.coalesce(func.max(Message.order_index), 0) + 1).where(Message.session_id == session_id)
        result = await db.execute(stmt)
        return int(result.scalar_one())

    @classmethod
    async def add_message(
        cls,
        db: AsyncSession,
        *,
        session_id: int,
        role: str,
        content: str,
        audio_url: str | None = None,
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            order_index=await cls.next_order_index(db, session_id),
            audio_url=audio_url,
        )
        db.add(message)
        await db.flush()

        stmt = (
            select(Message)
            .options(selectinload(Message.realtime_feedback))
            .where(Message.id == message.id)
        )
        result = await db.execute(stmt)
        return result.unique().scalar_one()

    @staticmethod
    async def upsert_message_realtime_feedback(
        db: AsyncSession,
        *,
        message_id: int,
        is_good: bool,
        better_answer: str | None,
        raw_response: dict[str, object] | None = None,
    ) -> MessageRealtimeFeedback:
        stmt = select(MessageRealtimeFeedback).where(MessageRealtimeFeedback.message_id == message_id)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        values = {
            "is_good": is_good,
            "better_answer": better_answer,
            "raw_response": raw_response,
        }
        if existing is None:
            existing = MessageRealtimeFeedback(message_id=message_id, **values)
            db.add(existing)
        else:
            for key, value in values.items():
                setattr(existing, key, value)
        await db.flush()
        return existing

    @staticmethod
    async def upsert_session_score(
        db: AsyncSession,
        *,
        session_id: int,
        values: dict[str, object],
    ) -> SessionScore:
        stmt = select(SessionScore).where(SessionScore.session_id == session_id)
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing is None:
            existing = SessionScore(session_id=session_id, **values)
            db.add(existing)
        else:
            for key, value in values.items():
                setattr(existing, key, value)
        await db.flush()
        return existing

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.modules.sessions.models.correction import Correction
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.message_score import MessageScore
from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.models.session import Session
from app.modules.sessions.models.session_score import SessionScore


FULL_SESSION_LOAD = (
    joinedload(Session.scenario),
    joinedload(Session.score),
    selectinload(Session.messages).selectinload(Message.corrections),
    selectinload(Session.messages).joinedload(Message.score),
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
            .options(joinedload(Session.scenario), joinedload(Session.score))
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
            stmt = stmt.options(joinedload(Session.scenario), joinedload(Session.score))
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
    async def count_messages(db: AsyncSession, session_id: int, *, role: str | None = None) -> int:
        stmt = select(func.count(Message.id)).where(Message.session_id == session_id)
        if role is not None:
            stmt = stmt.where(Message.role == role)
        result = await db.execute(stmt)
        return int(result.scalar_one() or 0)

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
        audio_duration_ms: int | None = None,
        asr_metadata: dict | list | str | None = None,
        corrections: list[dict] | None = None,
        score: dict | None = None,
    ) -> Message:
        message = Message(
            session_id=session_id,
            role=role,
            content=content,
            order_index=await cls.next_order_index(db, session_id),
            audio_url=audio_url,
            audio_duration_ms=audio_duration_ms,
            asr_metadata=asr_metadata,
        )
        db.add(message)
        await db.flush()

        for correction_data in corrections or []:
            db.add(Correction(message_id=message.id, **correction_data))

        if score:
            score_payload = dict(score)
            metadata = score_payload.pop("metadata", None)
            db.add(MessageScore(message_id=message.id, score_metadata=metadata, **score_payload))

        await db.flush()

        stmt = (
            select(Message)
            .options(selectinload(Message.corrections), joinedload(Message.score))
            .where(Message.id == message.id)
        )
        result = await db.execute(stmt)
        return result.unique().scalar_one()

    @staticmethod
    async def aggregate_message_scores(db: AsyncSession, session_id: int) -> dict[str, float | int] | None:
        stmt = (
            select(
                func.count(MessageScore.id).label("scored_message_count"),
                func.avg(MessageScore.pronunciation_score).label("avg_pronunciation"),
                func.avg(MessageScore.fluency_score).label("avg_fluency"),
                func.avg(MessageScore.grammar_score).label("avg_grammar"),
                func.avg(MessageScore.vocabulary_score).label("avg_vocabulary"),
                func.avg(MessageScore.intonation_score).label("avg_intonation"),
                func.avg(MessageScore.overall_score).label("overall_score"),
            )
            .join(Message, Message.id == MessageScore.message_id)
            .where(Message.session_id == session_id, Message.role == "user")
        )
        row = (await db.execute(stmt)).mappings().one()
        count = int(row["scored_message_count"] or 0)
        if count == 0:
            return None
        return {
            "scored_message_count": count,
            "avg_pronunciation": float(row["avg_pronunciation"] or 0.0),
            "avg_fluency": float(row["avg_fluency"] or 0.0),
            "avg_grammar": float(row["avg_grammar"] or 0.0),
            "avg_vocabulary": float(row["avg_vocabulary"] or 0.0),
            "avg_intonation": float(row["avg_intonation"] or 0.0),
            "overall_score": float(row["overall_score"] or 0.0),
        }

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

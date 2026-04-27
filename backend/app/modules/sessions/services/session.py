from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.infra.factory import LLMRole, create_llm_for_role
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.session import Session
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.sessions.repository import SessionRepository
from app.modules.sessions.schemas.lesson import LessonHintRead
from app.modules.sessions.schemas.session import (
    MessageCreate,
    RealtimeCorrectionRequest,
    RealtimeCorrectionResponse,
    SessionCreate,
    SessionFinishRequest,
    SessionHintRequest,
)
from app.modules.sessions.services.conversation_support import ConversationHintService, RealtimeCorrectionService
from app.modules.sessions.services.final_evaluation import SessionFinalEvaluationService
from app.modules.scenarios.services.scenario_service import user_is_vip
from app.modules.users.models.user import User

logger = logging.getLogger(__name__)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _duration_seconds(started_at: datetime, ended_at: datetime) -> int:
    if started_at.tzinfo is None:
        started_at = started_at.replace(tzinfo=timezone.utc)
    if ended_at.tzinfo is None:
        ended_at = ended_at.replace(tzinfo=timezone.utc)
    return max(0, int((ended_at - started_at).total_seconds()))


class SessionService:
    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0,
    ) -> list[Session]:
        return await SessionRepository.list_for_user(db, user_id, limit=limit, offset=offset)

    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: int, user_id: int) -> Session:
        session = await SessionRepository.get_by_id_for_user(db, session_id, user_id, full=True)
        if session is None:
            raise NotFoundError("Session not found")
        return session

    @staticmethod
    async def start_session(
        db: AsyncSession,
        *,
        user_id: int,
        payload: SessionCreate,
        user: User | None = None,
    ) -> Session:
        scenario = await ScenarioRepository.get_by_id(
            db,
            payload.scenario_id,
        )
        if scenario is None or scenario.deleted_at is not None or not scenario.is_active:
            logger.warning("Attempted to start session for inactive or missing scenario_id=%s", payload.scenario_id)
            raise NotFoundError("Scenario not found")
        if scenario.is_pro and not user_is_vip(user):
            raise ForbiddenError("This scenario requires VIP access")

        session_metadata: dict[str, Any] = dict(payload.metadata or {})

        session = await SessionRepository.create_session(
            db,
            user_id=user_id,
            scenario_id=scenario.id,
            status="active",
            session_metadata=session_metadata,
        )
        await db.commit()
        logger.info(
            "Started session id=%s user_id=%s scenario_id=%s",
            session.id,
            user_id,
            scenario.id,
        )
        return await SessionService.get_by_id(db, session.id, user_id)

    @staticmethod
    async def add_message(
        db: AsyncSession,
        *,
        session_id: int,
        user_id: int,
        payload: MessageCreate,
    ) -> Message:
        session = await SessionRepository.get_by_id_for_user(db, session_id, user_id, full=False)
        if session is None:
            raise NotFoundError("Session not found")
        if session.status != "active":
            raise BadRequestError("Cannot append messages to a non-active session")

        message = await SessionRepository.add_message(
            db,
            session_id=session.id,
            role=payload.role,
            content=payload.content.strip(),
            audio_url=payload.audio_url,
            audio_duration_ms=payload.audio_duration_ms,
            asr_metadata=payload.asr_metadata,
            corrections=[item.model_dump(exclude_none=True) for item in payload.corrections],
        )
        await db.commit()
        logger.info("Added message id=%s to session id=%s", message.id, session.id)
        return message

    @staticmethod
    async def build_hint(
        db: AsyncSession,
        *,
        session_id: int,
        user_id: int,
        payload: SessionHintRequest,
        user_level: str | None = None,
    ) -> LessonHintRead:
        session = await SessionRepository.get_by_id_for_user(db, session_id, user_id, full=True)
        if session is None:
            raise NotFoundError("Session not found")

        text = await SessionService._resolve_user_text(db, session=session, payload=payload)
        llm = create_llm_for_role(settings, LLMRole.DIALOGUE)
        try:
            service = ConversationHintService(
                llm=llm,
                max_tokens=settings.lesson_hint_llm_max_tokens or 700,
            )
            return await service.build_hint(session=session, user_level=user_level, user_text=text)
        finally:
            await llm.close()

    @staticmethod
    async def correct_realtime(
        db: AsyncSession,
        *,
        session_id: int,
        user_id: int,
        payload: RealtimeCorrectionRequest,
    ) -> RealtimeCorrectionResponse:
        session = await SessionRepository.get_by_id_for_user(db, session_id, user_id, full=True)
        if session is None:
            raise NotFoundError("Session not found")

        message = None
        if payload.message_id is not None:
            message = await SessionRepository.get_message_for_session(
                db,
                session_id=session.id,
                message_id=payload.message_id,
            )
            if message is None or message.role != "user":
                raise BadRequestError("Message does not belong to this session or is not a learner message")

        text = (payload.text or (message.content if message else "")).strip()
        if not text:
            raise BadRequestError("Provide message_id or text to correct")

        llm = create_llm_for_role(settings, LLMRole.ANALYSIS)
        try:
            service = RealtimeCorrectionService(
                llm=llm,
                max_tokens=settings.analysis_llm_max_tokens or 700,
            )
            response = await service.correct(scenario_title=session.scenario.title, text=text)
        finally:
            await llm.close()

        if message is None or not response.corrections:
            return response

        correction_dicts = [
            item.model_dump(exclude_none=True, exclude={"id"})
            for item in response.corrections
        ]
        created = await SessionRepository.add_corrections(
            db,
            message_id=message.id,
            corrections=correction_dicts,
        )
        await db.commit()

        by_index = list(response.corrections)
        for index, correction in enumerate(created):
            if index < len(by_index):
                by_index[index] = by_index[index].model_copy(update={"id": correction.id})
        return response.model_copy(update={"corrections": by_index, "persisted": True})

    @staticmethod
    async def end_session(
        db: AsyncSession,
        *,
        session_id: int,
        user_id: int,
        payload: SessionFinishRequest,
    ) -> Session:
        session = await SessionRepository.get_by_id_for_user(db, session_id, user_id, full=True)
        if session is None:
            raise NotFoundError("Session not found")
        await SessionService._finalize_session(
            db,
            session=session,
            payload=payload,
        )
        await SessionService._run_final_evaluation_if_needed(db, session=session)
        await db.commit()
        logger.info("Ended session id=%s user_id=%s status=%s", session.id, user_id, session.status)
        return await SessionService.get_by_id(db, session.id, user_id)

    @staticmethod
    async def finalize_after_ws_disconnect(
        db: AsyncSession,
        *,
        session_id: int,
        finalized_user_messages: int,
        metadata: dict[str, Any] | None = None,
    ) -> Session | None:
        session = await SessionRepository.get_by_id(db, session_id, full=True)
        if session is None:
            return None

        payload = SessionFinishRequest(
            status="completed" if finalized_user_messages > 0 else "abandoned",
            metadata=metadata or {},
        )
        await SessionService._finalize_session(db, session=session, payload=payload)
        await db.commit()
        return session

    @staticmethod
    async def merge_session_metadata(
        db: AsyncSession,
        *,
        session_id: int,
        user_id: int,
        metadata: dict[str, Any],
    ) -> Session:
        session = await SessionRepository.get_by_id_for_user(db, session_id, user_id, full=True)
        if session is None:
            raise NotFoundError("Session not found")

        merged_metadata = dict(session.session_metadata or {})
        merged_metadata.update(metadata)
        session.session_metadata = merged_metadata
        await db.commit()
        return await SessionService.get_by_id(db, session.id, user_id)

    @staticmethod
    async def run_final_evaluation(db: AsyncSession, *, session_id: int) -> None:
        session = await SessionRepository.get_by_id(db, session_id, full=True)
        if session is None:
            return
        await SessionService._run_final_evaluation_if_needed(db, session=session)

    @staticmethod
    async def _resolve_user_text(db: AsyncSession, *, session: Session, payload: SessionHintRequest) -> str | None:
        if payload.text and payload.text.strip():
            return payload.text.strip()
        if payload.message_id is None:
            return None
        message = await SessionRepository.get_message_for_session(
            db,
            session_id=session.id,
            message_id=payload.message_id,
        )
        if message is None or message.role != "user":
            raise BadRequestError("Message does not belong to this session or is not a learner message")
        return message.content.strip()

    @staticmethod
    async def _finalize_session(
        db: AsyncSession,
        *,
        session: Session,
        payload: SessionFinishRequest,
    ) -> None:
        ended_at = payload.ended_at or _utcnow()
        session.ended_at = ended_at

        user_message_count = await SessionRepository.count_messages(db, session.id, role="user")
        session.status = payload.status or ("completed" if user_message_count > 0 else "abandoned")
        session.duration_seconds = (
            _duration_seconds(session.started_at, ended_at) if user_message_count > 0 else None
        )

        merged_metadata = dict(session.session_metadata or {})
        merged_metadata.update(payload.metadata or {})
        session.session_metadata = merged_metadata

    @staticmethod
    async def _run_final_evaluation_if_needed(db: AsyncSession, *, session: Session) -> None:
        llm = None
        try:
            llm = create_llm_for_role(settings, LLMRole.EVALUATION)
            service = SessionFinalEvaluationService(
                llm=llm,
                max_tokens=settings.evaluation_llm_max_tokens or 1200,
            )
            await asyncio.wait_for(
                service.evaluate_and_store(db, session_id=session.id),
                timeout=max(1.0, settings.conversation_final_evaluation_timeout_seconds),
            )
        except asyncio.TimeoutError:
            logger.warning("Best-effort final evaluation timed out for session id=%s", session.id)
            await SessionService._mark_final_evaluation_failure(
                db,
                session=session,
                reason="final_evaluation_timeout",
            )
        except Exception:
            logger.exception("Best-effort final evaluation failed for session id=%s", session.id)
            await SessionService._mark_final_evaluation_failure(
                db,
                session=session,
                reason="final_evaluation_service_error",
            )
        finally:
            if llm is not None:
                await llm.close()

    @staticmethod
    async def _mark_final_evaluation_failure(
        db: AsyncSession,
        *,
        session: Session,
        reason: str,
    ) -> None:
        metadata = dict(session.session_metadata or {})
        final_evaluation = dict(metadata.get("final_evaluation") or {})
        final_evaluation.update(
            {
                "evaluation_status": "failed",
                "reason": reason,
                "updated_at": _utcnow().isoformat(),
            }
        )
        metadata["final_evaluation"] = final_evaluation
        session.session_metadata = metadata
        await db.flush()

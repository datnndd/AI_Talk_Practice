from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import BadRequestError, NotFoundError
from app.infra.factory import LLMRole, create_llm_for_role
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.session import Session
from app.modules.scenarios.repository import ScenarioRepository
from app.modules.sessions.repository import SessionRepository
from app.modules.sessions.schemas.session import MessageCreate, SessionCreate, SessionFinishRequest
from app.modules.scenarios.services.variation_service import VariationService
from app.modules.sessions.services.hybrid_conversation.final_evaluation import SessionFinalEvaluationService

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
    ) -> Session:
        scenario = await ScenarioRepository.get_by_id(
            db,
            payload.scenario_id,
            include_variations=True,
        )
        if scenario is None or scenario.deleted_at is not None or not scenario.is_active:
            logger.warning("Attempted to start session for inactive or missing scenario_id=%s", payload.scenario_id)
            raise NotFoundError("Scenario not found")

        # Basic validation for target_skills
        if payload.target_skills and scenario.target_skills:
            unsupported = [s for s in payload.target_skills if s not in scenario.target_skills]
            if unsupported:
                logger.info("User requested additional target skills for session: %s", unsupported)

        variation = await VariationService.resolve_variation_for_session(
            db,
            scenario=scenario,
            payload=payload,
        )

        session_metadata: dict[str, Any] = dict(payload.metadata or {})
        session_metadata["mode"] = payload.mode or scenario.mode
        if variation is not None:
            session_metadata["variation_seed"] = variation.variation_seed

        session = await SessionRepository.create_session(
            db,
            user_id=user_id,
            scenario_id=scenario.id,
            variation_id=variation.id if variation else None,
            status="active",
            target_skills=payload.target_skills or scenario.target_skills,
            session_metadata=session_metadata,
        )
        await db.commit()
        logger.info(
            "Started session id=%s user_id=%s scenario_id=%s variation_id=%s",
            session.id,
            user_id,
            scenario.id,
            variation.id if variation else None,
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
            score=payload.score.model_dump(exclude_none=True) if payload.score else None,
        )
        await db.commit()
        logger.info("Added message id=%s to session id=%s", message.id, session.id)
        return message

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

        aggregate = await SessionRepository.aggregate_message_scores(db, session.id)
        if aggregate is None:
            return

        relevance_score = payload.relevance_score if payload.relevance_score is not None else float(
            aggregate["overall_score"]
        )
        skill_breakdown = {
            "pronunciation": {"avg": aggregate["avg_pronunciation"]},
            "fluency": {"avg": aggregate["avg_fluency"]},
            "grammar": {"avg": aggregate["avg_grammar"]},
            "vocabulary": {"avg": aggregate["avg_vocabulary"]},
            "intonation": {"avg": aggregate["avg_intonation"]},
        }
        session.score = await SessionRepository.upsert_session_score(
            db,
            session_id=session.id,
            values={
                "avg_pronunciation": aggregate["avg_pronunciation"],
                "avg_fluency": aggregate["avg_fluency"],
                "avg_grammar": aggregate["avg_grammar"],
                "avg_vocabulary": aggregate["avg_vocabulary"],
                "avg_intonation": aggregate["avg_intonation"],
                "relevance_score": relevance_score,
                "overall_score": aggregate["overall_score"],
                "scored_message_count": aggregate["scored_message_count"],
                "skill_breakdown": skill_breakdown,
                "feedback_summary": payload.feedback_summary,
                "score_metadata": {"aggregated_at": _utcnow().isoformat()},
            },
        )

    @staticmethod
    async def _run_final_evaluation_if_needed(db: AsyncSession, *, session: Session) -> None:
        metadata = session.session_metadata or {}
        if metadata.get("conversation_engine") != "lesson_v1" and "hybrid_conversation" not in metadata:
            return
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
        except Exception:
            logger.exception("Best-effort final evaluation failed for session id=%s", session.id)
            metadata = dict(session.session_metadata or {})
            final_evaluation = dict(metadata.get("final_evaluation") or {})
            final_evaluation.update(
                {
                    "evaluation_status": "failed",
                    "reason": "timeout_or_service_error",
                    "updated_at": _utcnow().isoformat(),
                }
            )
            metadata["final_evaluation"] = final_evaluation
            session.session_metadata = metadata
            await db.flush()

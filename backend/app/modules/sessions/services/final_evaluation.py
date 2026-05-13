from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sessions.models.session_score import SessionScore
from app.modules.sessions.repository import SessionRepository
from app.modules.sessions.services.conversation_support import ConversationFinalEvaluationBuilder

logger = logging.getLogger(__name__)
conversation_logger = logging.getLogger("conversation_trace")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionFinalEvaluationService:
    """Runs post-session evaluation and stores session scores."""

    def __init__(self, *, llm, max_tokens: int):
        self.llm = llm
        self.max_tokens = max_tokens

    async def evaluate_and_store(self, db: AsyncSession, *, session_id: int) -> SessionScore | None:
        session = await SessionRepository.get_by_id(db, session_id, full=True)
        if session is None:
            return None

        user_messages = [message for message in session.messages if message.role == "user" and message.content.strip()]
        if not user_messages:
            await self._mark_status(db, session, status="skipped", reason="no_user_messages")
            return None

        try:
            evaluation_builder = ConversationFinalEvaluationBuilder(
                llm=self.llm,
                max_tokens=self.max_tokens,
            )
            payload = await evaluation_builder.evaluate(session=session)
        except Exception:
            logger.exception("Final session evaluation failed for session_id=%s", session.id)
            await self._mark_status(db, session, status="failed", reason="llm_or_parse_error")
            return None

        skill_breakdown = {
            "fluency": {"avg": payload.fluency_score},
            "grammar": {"avg": payload.grammar_score},
            "vocabulary": {"avg": payload.vocabulary_score},
            "intonation": {"avg": payload.intonation_score},
            "relevance": {"avg": payload.relevance_score},
        }
        metadata = {
            "source": "final_evaluation_llm",
            "evaluated_at": _utcnow(),
            "evaluation_status": "completed",
            "objective_completion": payload.objective_completion,
            "strengths": payload.strengths,
            "improvements": payload.improvements,
            "corrections": payload.corrections,
            "next_steps": payload.next_steps,
        }
        score = await SessionRepository.upsert_session_score(
            db,
            session_id=session.id,
            values={
                "avg_fluency": payload.fluency_score,
                "avg_grammar": payload.grammar_score,
                "avg_vocabulary": payload.vocabulary_score,
                "avg_intonation": payload.intonation_score,
                "relevance_score": payload.relevance_score,
                "overall_score": payload.overall_score,
                "scored_message_count": len(user_messages),
                "skill_breakdown": skill_breakdown,
                "feedback_summary": payload.feedback_summary,
                "score_metadata": metadata,
            },
        )
        await self._mark_status(db, session, status="completed", reason=None)
        await db.flush()
        conversation_logger.info(
            "event=final_evaluation_completed session_id=%s user_id=%s overall_score=%s scored_message_count=%s",
            session.id,
            session.user_id,
            score.overall_score,
            score.scored_message_count,
        )
        return score

    async def _mark_status(self, db: AsyncSession, session, *, status: str, reason: str | None) -> None:
        metadata = dict(session.session_metadata or {})
        final_evaluation = dict(metadata.get("final_evaluation") or {})
        final_evaluation.update({"evaluation_status": status, "updated_at": _utcnow()})
        if reason:
            final_evaluation["reason"] = reason
        metadata["final_evaluation"] = final_evaluation
        session.session_metadata = metadata
        await db.flush()

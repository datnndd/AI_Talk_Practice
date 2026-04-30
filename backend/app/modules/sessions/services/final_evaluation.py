from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sessions.models.session_score import SessionScore
from app.modules.sessions.repository import SessionRepository
from app.modules.sessions.services.conversation_support import (
    ConversationFinalEvaluationBuilder,
    ConversationPersonalInfoService,
)
from app.modules.users.models.user import User

logger = logging.getLogger(__name__)
conversation_logger = logging.getLogger("conversation_trace")


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class SessionFinalEvaluationService:
    """Runs post-session evaluation and stores both scores and learner profile signals."""

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
            "pronunciation": {"avg": payload.pronunciation_score},
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
                "avg_pronunciation": payload.pronunciation_score,
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
        await self._extract_profile_best_effort(db, session=session)
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

    async def _mark_profile_status(self, db: AsyncSession, session, *, status: str, reason: str | None = None) -> None:
        metadata = dict(session.session_metadata or {})
        final_evaluation = dict(metadata.get("final_evaluation") or {})
        final_evaluation.update({"profile_extraction_status": status, "profile_updated_at": _utcnow()})
        if reason:
            final_evaluation["profile_extraction_reason"] = reason
        metadata["final_evaluation"] = final_evaluation
        session.session_metadata = metadata
        await db.flush()

    async def _extract_profile_best_effort(self, db: AsyncSession, *, session) -> None:
        user = await db.scalar(select(User).where(User.id == session.user_id))
        if user is None:
            await self._mark_profile_status(db, session, status="skipped", reason="user_not_found")
            return

        try:
            personal_info_service = ConversationPersonalInfoService(
                llm=self.llm,
                max_tokens=min(self.max_tokens, 700),
            )
            profile_payload = await personal_info_service.extract(
                session=session,
                existing_preferences=dict(user.preferences or {}),
            )
            user.preferences = _merge_conversation_profile(
                existing_preferences=dict(user.preferences or {}),
                personal_info=profile_payload.personal_info,
                preferences=profile_payload.preferences,
                notes=profile_payload.notes,
            )
        except Exception:
            logger.exception("Conversation profile extraction failed for session_id=%s", session.id)
            await self._mark_profile_status(db, session, status="failed", reason="llm_or_parse_error")
            return

        await self._mark_profile_status(db, session, status="completed")
        conversation_logger.info(
            "event=conversation_profile_extracted session_id=%s user_id=%s",
            session.id,
            session.user_id,
        )


def _merge_conversation_profile(
    *,
    existing_preferences: dict[str, Any],
    personal_info: dict[str, Any],
    preferences: dict[str, Any],
    notes: list[str],
) -> dict[str, Any]:
    merged = dict(existing_preferences or {})
    conversation_profile = dict(merged.get("conversation_profile") or {})
    current_personal_info = dict(conversation_profile.get("personal_info") or {})
    current_personal_info.update({key: value for key, value in (personal_info or {}).items() if value not in (None, "", [], {})})

    current_preferences = dict(conversation_profile.get("preferences") or {})
    for key, value in (preferences or {}).items():
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            existing = current_preferences.get(key)
            items = list(existing) if isinstance(existing, list) else ([] if existing in (None, "") else [existing])
            for item in value:
                if item and item not in items:
                    items.append(item)
            current_preferences[key] = items
        else:
            current_preferences[key] = value

    existing_notes = list(conversation_profile.get("notes") or [])
    for note in notes or []:
        if note and note not in existing_notes:
            existing_notes.append(note)

    conversation_profile.update(
        {
            "personal_info": current_personal_info,
            "preferences": current_preferences,
            "notes": existing_notes[-20:],
            "updated_at": _utcnow(),
        }
    )
    merged["conversation_profile"] = conversation_profile
    return merged

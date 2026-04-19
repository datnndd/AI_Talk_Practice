from __future__ import annotations

from app.modules.scenarios.serializers import serialize_scenario
from app.modules.sessions.models.correction import Correction
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.message_score import MessageScore
from app.modules.sessions.models.session import Session
from app.modules.sessions.models.session_score import SessionScore
from app.modules.sessions.schemas import (
    CorrectionRead,
    MessageRead,
    MessageScoreRead,
    SessionListItem,
    SessionRead,
    SessionScoreRead,
)


def serialize_correction(correction: Correction) -> CorrectionRead:
    return CorrectionRead.model_validate(correction)


def serialize_message_score(score: MessageScore) -> MessageScoreRead:
    return MessageScoreRead.model_validate(
        {
            "id": score.id,
            "pronunciation_score": score.pronunciation_score,
            "fluency_score": score.fluency_score,
            "grammar_score": score.grammar_score,
            "vocabulary_score": score.vocabulary_score,
            "intonation_score": score.intonation_score,
            "overall_score": score.overall_score,
            "mispronounced_words": score.mispronounced_words,
            "feedback": score.feedback,
            "metadata": score.score_metadata or {},
            "created_at": score.created_at,
            "updated_at": score.updated_at,
        }
    )


def serialize_message(message: Message) -> MessageRead:
    return MessageRead.model_validate(
        {
            "id": message.id,
            "session_id": message.session_id,
            "role": message.role,
            "content": message.content,
            "order_index": message.order_index,
            "audio_url": message.audio_url,
            "audio_duration_ms": message.audio_duration_ms,
            "asr_metadata": message.asr_metadata,
            "corrections": [serialize_correction(item) for item in message.corrections],
            "score": serialize_message_score(message.score) if message.score else None,
            "created_at": message.created_at,
            "updated_at": message.updated_at,
        }
    )


def serialize_session_score(score: SessionScore) -> SessionScoreRead:
    return SessionScoreRead.model_validate(
        {
            "id": score.id,
            "avg_pronunciation": score.avg_pronunciation,
            "avg_fluency": score.avg_fluency,
            "avg_grammar": score.avg_grammar,
            "avg_vocabulary": score.avg_vocabulary,
            "avg_intonation": score.avg_intonation,
            "relevance_score": score.relevance_score,
            "overall_score": score.overall_score,
            "scored_message_count": score.scored_message_count,
            "skill_breakdown": score.skill_breakdown or {},
            "feedback_summary": score.feedback_summary,
            "metadata": score.score_metadata or {},
            "created_at": score.created_at,
            "updated_at": score.updated_at,
        }
    )


def _session_mode(session: Session) -> str:
    metadata = session.session_metadata or {}
    return metadata.get("mode") or session.scenario.mode


def serialize_session_list_item(session: Session) -> SessionListItem:
    return SessionListItem.model_validate(
        {
            "id": session.id,
            "scenario_id": session.scenario_id,
            "scenario_title": session.scenario.title,
            "status": session.status,
            "mode": _session_mode(session),
            "duration_seconds": session.duration_seconds,
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "overall_score": session.score.overall_score if session.score else None,
        }
    )


def serialize_session(session: Session) -> SessionRead:
    return SessionRead.model_validate(
        {
            "id": session.id,
            "user_id": session.user_id,
            "scenario_id": session.scenario_id,
            "status": session.status,
            "mode": _session_mode(session),
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "duration_seconds": session.duration_seconds,
            "target_skills": session.target_skills,
            "metadata": session.session_metadata or {},
            "scenario": serialize_scenario(session.scenario),
            "messages": [serialize_message(item) for item in session.messages],
            "score": serialize_session_score(session.score) if session.score else None,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }
    )

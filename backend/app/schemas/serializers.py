from __future__ import annotations

from app.modules.sessions.models.correction import Correction
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.message_score import MessageScore
from app.modules.scenarios.models import Scenario, ScenarioPromptHistory, ScenarioVariation
from app.modules.sessions.models.session import Session
from app.modules.sessions.models.session_score import SessionScore
from app.modules.users.models.user import User
from app.modules.scenarios.schemas import (
    PromptHistoryRead,
    PromptQualityAssessment,
    ScenarioAdminRead,
    ScenarioVariationAdminRead,
)
from app.modules.scenarios.schemas import ScenarioRead, ScenarioVariationRead
from app.modules.sessions.schemas import (
    CorrectionRead,
    MessageRead,
    MessageScoreRead,
    SessionListItem,
    SessionRead,
    SessionScoreRead,
)
from app.modules.users.schemas import UserRead


def user_is_admin(user: User) -> bool:
    preferences = user.preferences or {}
    return bool(preferences.get("is_admin") or preferences.get("role") == "admin")


def serialize_user(user: User) -> UserRead:
    return UserRead.model_validate(
        {
            "id": user.id,
            "email": user.email,
            "is_admin": user_is_admin(user),
            "display_name": user.display_name,
            "avatar": user.avatar,
            "age": user.age,
            "native_language": user.native_language,
            "target_language": user.target_language,
            "level": user.level,
            "favorite_topics": user.favorite_topics,
            "learning_purpose": user.learning_purpose,
            "main_challenge": user.main_challenge,
            "daily_goal": user.daily_goal,
            "is_onboarding_completed": user.is_onboarding_completed,
            "preferences": user.preferences or {},
            "subscription": user.subscription,  # SQLAlchemy relationship
            "created_at": user.created_at,
            "updated_at": user.updated_at,
        }
    )


def serialize_variation(variation: ScenarioVariation) -> ScenarioVariationRead:
    return ScenarioVariationRead.model_validate(variation)


def serialize_admin_prompt_history(item: ScenarioPromptHistory) -> PromptHistoryRead:
    return PromptHistoryRead.model_validate(item)


def serialize_admin_variation(variation: ScenarioVariation) -> ScenarioVariationAdminRead:
    return ScenarioVariationAdminRead.model_validate(
        {
            "id": variation.id,
            "scenario_id": variation.scenario_id,
            "variation_seed": variation.variation_seed,
            "variation_name": variation.variation_name,
            "parameters": variation.parameters or {},
            "sample_prompt": variation.sample_prompt,
            "sample_conversation": variation.sample_conversation or [],
            "system_prompt_override": variation.system_prompt_override,
            "is_active": variation.is_active,
            "is_pregenerated": variation.is_pregenerated,
            "is_approved": variation.is_approved,
            "generated_by_model": variation.generated_by_model,
            "generation_latency_ms": variation.generation_latency_ms,
            "usage_count": variation.usage_count,
            "last_used_at": variation.last_used_at,
            "created_at": variation.created_at,
            "updated_at": variation.updated_at,
        }
    )


def serialize_admin_scenario(
    scenario: Scenario,
    *,
    usage_count: int = 0,
    latest_prompt_quality: PromptQualityAssessment | None = None,
    include_variations: bool = True,
    include_prompt_history: bool = True,
) -> ScenarioAdminRead:
    variations = getattr(scenario, "variations", []) or []
    active_variation_count = sum(1 for item in variations if item.is_active)
    return ScenarioAdminRead.model_validate(
        {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "ai_system_prompt": scenario.ai_system_prompt,
            "learning_objectives": scenario.learning_objectives or [],
            "target_skills": scenario.target_skills or [],
            "tags": scenario.tags or [],
            "estimated_duration_minutes": int(scenario.estimated_duration / 60)
            if scenario.estimated_duration
            else None,
            "is_pre_generated": scenario.is_pre_generated,
            "pre_gen_count": scenario.pre_gen_count,
            "mode": scenario.mode,
            "metadata": scenario.scenario_metadata or {},
            "is_active": scenario.is_active,
            "deleted_at": scenario.deleted_at,
            "created_by": scenario.created_by,
            "usage_count": usage_count,
            "variation_count": len(variations),
            "active_variation_count": active_variation_count,
            "latest_prompt_quality": latest_prompt_quality,
            "variations": [serialize_admin_variation(item) for item in variations] if include_variations else [],
            "prompt_history": [
                serialize_admin_prompt_history(item) for item in getattr(scenario, "prompt_history", [])
            ]
            if include_prompt_history
            else [],
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
        }
    )


def serialize_scenario(
    scenario: Scenario,
    *,
    include_variations: bool = False,
) -> ScenarioRead:
    return ScenarioRead.model_validate(
        {
            "id": scenario.id,
            "title": scenario.title,
            "description": scenario.description,
            "learning_objectives": scenario.learning_objectives,
            "ai_system_prompt": scenario.ai_system_prompt,
            "category": scenario.category,
            "difficulty": scenario.difficulty,
            "target_skills": scenario.target_skills,
            "tags": scenario.tags,
            "estimated_duration": scenario.estimated_duration,
            "mode": scenario.mode,
            "metadata": scenario.scenario_metadata or {},
            "is_active": scenario.is_active,
            "created_by": scenario.created_by,
            "created_at": scenario.created_at,
            "updated_at": scenario.updated_at,
            "variations": [serialize_variation(item) for item in getattr(scenario, "variations", [])]
            if include_variations
            else [],
        }
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


def _session_variation_seed(session: Session) -> str | None:
    if session.variation:
        return session.variation.variation_seed
    metadata = session.session_metadata or {}
    return metadata.get("variation_seed")


def serialize_session_list_item(session: Session) -> SessionListItem:
    return SessionListItem.model_validate(
        {
            "id": session.id,
            "scenario_id": session.scenario_id,
            "scenario_title": session.scenario.title,
            "status": session.status,
            "mode": _session_mode(session),
            "variation_id": session.variation_id,
            "variation_seed": _session_variation_seed(session),
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
            "variation_id": session.variation_id,
            "status": session.status,
            "mode": _session_mode(session),
            "started_at": session.started_at,
            "ended_at": session.ended_at,
            "duration_seconds": session.duration_seconds,
            "target_skills": session.target_skills,
            "metadata": session.session_metadata or {},
            "variation_seed": _session_variation_seed(session),
            "scenario": serialize_scenario(session.scenario, include_variations=False),
            "variation": serialize_variation(session.variation) if session.variation else None,
            "messages": [serialize_message(item) for item in session.messages],
            "score": serialize_session_score(session.score) if session.score else None,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
        }
    )

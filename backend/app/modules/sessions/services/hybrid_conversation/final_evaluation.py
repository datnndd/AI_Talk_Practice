from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.contracts import LLMBase, Message
from app.modules.sessions.models.session_score import SessionScore
from app.modules.sessions.repository import SessionRepository

logger = logging.getLogger(__name__)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class FinalEvaluationPayload(BaseModel):
    pronunciation_score: float = Field(ge=0.0, le=10.0)
    fluency_score: float = Field(ge=0.0, le=10.0)
    grammar_score: float = Field(ge=0.0, le=10.0)
    vocabulary_score: float = Field(ge=0.0, le=10.0)
    intonation_score: float = Field(ge=0.0, le=10.0)
    relevance_score: float = Field(ge=0.0, le=10.0)
    overall_score: float = Field(ge=0.0, le=10.0)
    objective_completion: str = "unknown"
    strengths: list[str] = Field(default_factory=list)
    improvements: list[str] = Field(default_factory=list)
    corrections: list[dict[str, Any]] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    feedback_summary: str = ""


class SessionFinalEvaluationService:
    """Runs a post-session LLM evaluation and stores the result in SessionScore."""

    def __init__(self, *, llm: LLMBase, max_tokens: int):
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

        aggregate = await SessionRepository.aggregate_message_scores(db, session.id)
        try:
            payload = await self._evaluate(session=session, aggregate=aggregate)
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
            "aggregate_message_scores": aggregate,
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
        return score

    async def _evaluate(self, *, session, aggregate: dict[str, float | int] | None) -> FinalEvaluationPayload:
        system_prompt = self._system_prompt(session=session, aggregate=aggregate)
        compact_messages = self._compact_messages(session)
        chunks = []
        async for chunk in self.llm.chat_stream(
            [Message(role="user", content=compact_messages)],
            system_prompt=system_prompt,
            max_tokens=self.max_tokens,
        ):
            chunks.append(chunk)
        return FinalEvaluationPayload.model_validate(_parse_json_object("".join(chunks)))

    def _system_prompt(self, *, session, aggregate: dict[str, float | int] | None) -> str:
        scenario = session.scenario
        metadata = session.session_metadata or {}
        hybrid = metadata.get("hybrid_conversation") or {}
        evidence = json.dumps(aggregate, ensure_ascii=False) if aggregate else "None"
        objectives = scenario.learning_objectives if scenario.learning_objectives else []
        return "\n".join(
            [
                "Evaluate one completed English speaking practice session.",
                "Return only one JSON object. Do not include markdown.",
                "Give learner-facing feedback_summary in Vietnamese.",
                "Use numeric scores from 0 to 10.",
                f"Scenario: {scenario.title}",
                f"Scenario description: {scenario.description}",
                f"Learning objectives: {objectives}",
                f"Target skills: {session.target_skills or scenario.target_skills or []}",
                f"Hybrid memory/dialogue state: {json.dumps(hybrid, ensure_ascii=False)[:2400]}",
                f"Message score evidence: {evidence}",
                "JSON schema: {",
                '  "pronunciation_score": 0.0,',
                '  "fluency_score": 0.0,',
                '  "grammar_score": 0.0,',
                '  "vocabulary_score": 0.0,',
                '  "intonation_score": 0.0,',
                '  "relevance_score": 0.0,',
                '  "overall_score": 0.0,',
                '  "objective_completion": "completed|partial|not_completed",',
                '  "strengths": ["..."],',
                '  "improvements": ["..."],',
                '  "corrections": [{"original":"...","suggestion":"...","explanation":"..."}],',
                '  "next_steps": ["..."],',
                '  "feedback_summary": "Vietnamese summary"',
                "}",
            ]
        )

    def _compact_messages(self, session) -> str:
        lines = []
        for message in sorted(session.messages, key=lambda item: item.order_index):
            if not message.content.strip():
                continue
            role = "Learner" if message.role == "user" else "Assistant"
            lines.append(f"{role}: {message.content.strip()}")
        return "\n".join(lines[-16:])

    async def _mark_status(self, db: AsyncSession, session, *, status: str, reason: str | None) -> None:
        metadata = dict(session.session_metadata or {})
        final_evaluation = dict(metadata.get("final_evaluation") or {})
        final_evaluation.update({"evaluation_status": status, "updated_at": _utcnow()})
        if reason:
            final_evaluation["reason"] = reason
        metadata["final_evaluation"] = final_evaluation
        session.session_metadata = metadata
        await db.flush()


def _parse_json_object(raw: str) -> dict[str, Any]:
    raw = raw.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fenced:
        raw = fenced.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end >= start:
            raw = raw[start : end + 1]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid final evaluation JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Final evaluation must be a JSON object")
    return parsed

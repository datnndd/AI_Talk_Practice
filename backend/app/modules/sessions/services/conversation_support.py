from __future__ import annotations

import json
import logging
import re
from typing import Any, AsyncIterator, Literal

from pydantic import BaseModel, Field

from app.infra.contracts import LLMBase, Message
from app.modules.sessions.schemas.lesson import LessonHintRead
from app.modules.sessions.schemas.session import RealtimeCorrectionItem, RealtimeCorrectionResponse
from app.modules.sessions.services.conversation_prompts import (
    build_conversation_end_check_prompt,
    build_dialogue_system_prompt,
    build_full_assessment_prompt,
    build_hint_prompt,
    build_personal_info_extraction_prompt,
    build_realtime_correction_prompt,
    build_summary_prompt,
)

logger = logging.getLogger(__name__)


class HintPayload(BaseModel):
    analysis_vi: str
    answer_strategy_vi: str
    keywords: list[str] = Field(default_factory=list)
    sample_answers: list[str] = Field(default_factory=list)
    sample_answer: str
    sample_answer_easy: str


class CorrectionPayload(BaseModel):
    corrected_text: str
    corrections: list[RealtimeCorrectionItem] = Field(default_factory=list)


class SummaryPayload(BaseModel):
    summary: str = ""


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


class PersonalInfoPayload(BaseModel):
    personal_info: dict[str, Any] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)
    notes: list[str] = Field(default_factory=list)


class ConversationEndDecisionPayload(BaseModel):
    should_end: Literal["yes", "no"] = "no"
    reason: str = ""


def session_rolling_summary(session) -> str:
    metadata = session.session_metadata or {}
    return str(metadata.get("rolling_summary") or "").strip()


def session_user_turn_count(session) -> int:
    return sum(1 for message in session.messages if message.role == "user" and message.content.strip())


def session_total_turn_count(session) -> int:
    return sum(1 for message in session.messages if (message.content or "").strip())


def session_recent_turns_text(session, *, limit: int = 12) -> str:
    lines: list[str] = []
    for message in _sorted_messages(session)[-max(1, limit):]:
        content = (message.content or "").strip()
        if not content:
            continue
        role = "Learner" if message.role == "user" else "Assistant"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def session_full_turns_text(session) -> str:
    lines: list[str] = []
    for message in _sorted_messages(session):
        content = (message.content or "").strip()
        if not content:
            continue
        role = "Learner" if message.role == "user" else "Assistant"
        lines.append(f"{role}: {content}")
    return "\n".join(lines)


def session_current_question(session) -> str:
    for message in reversed(_sorted_messages(session)):
        if message.role == "assistant" and message.content.strip():
            return message.content.strip()
    return (session.scenario.description or "").strip()


def session_recent_llm_messages(session, *, limit: int = 10) -> list[Message]:
    messages: list[Message] = []
    for item in _sorted_messages(session)[-max(1, limit):]:
        content = (item.content or "").strip()
        if not content:
            continue
        messages.append(Message(role=item.role, content=content))
    return messages


class ConversationReplyService:
    def __init__(self, *, llm: LLMBase, message_limit: int = 10):
        self.llm = llm
        self.message_limit = max(1, int(message_limit))

    async def generate_opening_reply(
        self,
        *,
        session,
        user_preferences: dict[str, Any] | None = None,
    ) -> str:
        system_prompt = self._system_prompt(session=session, user_preferences=user_preferences)
        chunks: list[str] = []
        async for chunk in self.llm.chat_stream(
            [
                Message(
                    role="user",
                    content=(
                        "The narration has finished. Start the role-play now with the first natural assistant turn. "
                        "Do not mention that the narration ended."
                    ),
                )
            ],
            system_prompt=system_prompt,
        ):
            chunks.append(chunk)
        return "".join(chunks).strip()

    async def stream_reply(
        self,
        *,
        session,
        user_preferences: dict[str, Any] | None = None,
        extra_instruction: str | None = None,
    ) -> AsyncIterator[str]:
        system_prompt = self._system_prompt(
            session=session,
            user_preferences=user_preferences,
            extra_instruction=extra_instruction,
        )
        messages = session_recent_llm_messages(session, limit=self.message_limit)
        async for chunk in self.llm.chat_stream(messages, system_prompt=system_prompt):
            yield chunk

    def _system_prompt(
        self,
        *,
        session,
        user_preferences: dict[str, Any] | None = None,
        extra_instruction: str | None = None,
    ) -> str:
        return build_dialogue_system_prompt(
            scenario=session.scenario,
            rolling_summary=session_rolling_summary(session),
            recent_turns=session_recent_turns_text(session, limit=self.message_limit * 2),
            target_skills=list(session.target_skills or session.scenario.target_skills or []),
            user_preferences=user_preferences,
            extra_instruction=extra_instruction,
        )


class ConversationEndingService:
    def __init__(self, *, llm: LLMBase, max_tokens: int = 250, min_turns: int = 6):
        self.llm = llm
        self.max_tokens = max_tokens
        self.min_turns = max(1, int(min_turns))
        self._signal_patterns = [
            re.compile(pattern, flags=re.IGNORECASE)
            for pattern in (
                r"\bgoodbye\b",
                r"\bbye(?:\s+bye)?\b",
                r"\bsee you (?:later|soon|next time)\b",
                r"\btalk to you later\b",
                r"\bcatch you later\b",
                r"\bsee ya\b",
                r"\bfarewell\b",
                r"\bhave a (?:nice|good) day\b",
                r"\bthat's all\b",
                r"\bnothing else\b",
                r"\bno,? thank you\b",
                r"\bthanks?,?\s+bye\b",
                r"\bthank you,?\s+bye\b",
            )
        ]

    def should_consider(self, *, session, user_text: str) -> bool:
        if session_total_turn_count(session) < self.min_turns:
            return False
        normalized_text = (user_text or "").strip()
        if not normalized_text:
            return False
        return any(pattern.search(normalized_text) for pattern in self._signal_patterns)

    async def should_end(self, *, session) -> bool:
        recent_turns = session_recent_turns_text(session, limit=6)
        payload = await _collect_json(
            self.llm,
            model=ConversationEndDecisionPayload,
            system_prompt=build_conversation_end_check_prompt(
                scenario=session.scenario,
                recent_turns=recent_turns,
            ),
            user_text=recent_turns or session.scenario.title,
            max_tokens=self.max_tokens,
        )
        return payload.should_end == "yes"


class ConversationHintService:
    def __init__(self, *, llm: LLMBase, max_tokens: int = 700):
        self.llm = llm
        self.max_tokens = max_tokens

    async def build_hint(
        self,
        *,
        session,
        user_level: str | None = None,
        user_text: str | None = None,
    ) -> LessonHintRead:
        del user_level
        current_question = session_current_question(session)
        system_prompt = build_hint_prompt(
            scenario=session.scenario,
            rolling_summary=session_rolling_summary(session),
            recent_turns=session_recent_turns_text(session, limit=10),
            current_question=current_question,
            user_text=user_text,
        )
        payload = await _collect_json(
            self.llm,
            model=HintPayload,
            system_prompt=system_prompt,
            user_text=user_text or current_question or session.scenario.title,
            max_tokens=self.max_tokens,
        )
        sample_answers = payload.sample_answers or [payload.sample_answer]
        return LessonHintRead(
            lesson_id=f"session-{session.id}",
            objective_id="conversation_hint",
            question=current_question,
            analysis_vi=payload.analysis_vi,
            answer_strategy_vi=payload.answer_strategy_vi,
            keywords=payload.keywords[:6],
            sample_answers=sample_answers[:3],
            sample_answer=payload.sample_answer or sample_answers[0],
            sample_answer_easy=payload.sample_answer_easy or payload.sample_answer,
            cached=False,
            metadata={"source": "conversation_hint_prompt"},
        )


class RealtimeCorrectionService:
    def __init__(self, *, llm: LLMBase, max_tokens: int = 700):
        self.llm = llm
        self.max_tokens = max_tokens

    async def correct(
        self,
        *,
        scenario_title: str,
        text: str,
    ) -> RealtimeCorrectionResponse:
        system_prompt = build_realtime_correction_prompt(scenario_title=scenario_title, text=text)
        payload = await _collect_json(
            self.llm,
            model=CorrectionPayload,
            system_prompt=system_prompt,
            user_text=text,
            max_tokens=self.max_tokens,
        )
        corrections = [_normalize_correction(item, fallback_text=text) for item in payload.corrections]
        return RealtimeCorrectionResponse(
            corrected_text=payload.corrected_text or text,
            corrections=corrections,
            persisted=False,
        )


class ConversationSummaryService:
    def __init__(self, *, llm: LLMBase, max_tokens: int = 400, turn_interval: int = 8, summary_max_chars: int = 600):
        self.llm = llm
        self.max_tokens = max_tokens
        self.turn_interval = max(1, int(turn_interval))
        self.summary_max_chars = max(120, int(summary_max_chars))

    def should_summarize(self, session) -> bool:
        turn_count = session_user_turn_count(session)
        return turn_count > 0 and turn_count % self.turn_interval == 0

    async def summarize(self, *, session) -> str:
        system_prompt = build_summary_prompt(
            scenario=session.scenario,
            previous_summary=session_rolling_summary(session),
            recent_turns=session_recent_turns_text(session, limit=16),
            max_chars=self.summary_max_chars,
        )
        payload = await _collect_json(
            self.llm,
            model=SummaryPayload,
            system_prompt=system_prompt,
            user_text=session_recent_turns_text(session, limit=16) or session.scenario.title,
            max_tokens=self.max_tokens,
        )
        return payload.summary[: self.summary_max_chars].strip()


class ConversationFinalEvaluationBuilder:
    def __init__(self, *, llm: LLMBase, max_tokens: int = 1200):
        self.llm = llm
        self.max_tokens = max_tokens

    async def evaluate(self, *, session) -> FinalEvaluationPayload:
        system_prompt = build_full_assessment_prompt(
            scenario_title=session.scenario.title,
            scenario_description=session.scenario.description,
            learning_objectives=session.scenario.learning_objectives or [],
            target_skills=session.target_skills or session.scenario.target_skills or [],
            rolling_summary=session_rolling_summary(session),
        )
        compact_messages = session_full_turns_text(session)
        return await _collect_json(
            self.llm,
            model=FinalEvaluationPayload,
            system_prompt=system_prompt,
            user_text=compact_messages or session.scenario.title,
            max_tokens=self.max_tokens,
        )


class ConversationPersonalInfoService:
    def __init__(self, *, llm: LLMBase, max_tokens: int = 700):
        self.llm = llm
        self.max_tokens = max_tokens

    async def extract(
        self,
        *,
        session,
        existing_preferences: dict[str, Any] | None = None,
    ) -> PersonalInfoPayload:
        system_prompt = build_personal_info_extraction_prompt(existing_preferences=existing_preferences)
        transcript = session_full_turns_text(session)
        return await _collect_json(
            self.llm,
            model=PersonalInfoPayload,
            system_prompt=system_prompt,
            user_text=transcript or session.scenario.title,
            max_tokens=self.max_tokens,
        )


async def _collect_json(
    llm: LLMBase,
    *,
    model: type[BaseModel],
    system_prompt: str,
    user_text: str,
    max_tokens: int,
) -> Any:
    chunks: list[str] = []
    async for chunk in llm.chat_stream(
        [Message(role="user", content=user_text.strip())],
        system_prompt=system_prompt,
        max_tokens=max_tokens,
    ):
        chunks.append(chunk)
    return model.model_validate(_parse_json_object("".join(chunks)))


def _sorted_messages(session) -> list[Any]:
    return sorted(session.messages or [], key=lambda item: item.order_index)


def _normalize_correction(item: RealtimeCorrectionItem, *, fallback_text: str) -> RealtimeCorrectionItem:
    error_type = item.error_type if item.error_type in {"grammar", "vocabulary", "naturalness", "pronunciation", "register"} else "grammar"
    severity = item.severity if item.severity in {"low", "medium", "high"} else "medium"
    return item.model_copy(
        update={
            "original_text": item.original_text or fallback_text,
            "corrected_text": item.corrected_text or fallback_text,
            "explanation": item.explanation or "Câu này có thể rõ và tự nhiên hơn.",
            "error_type": error_type,
            "severity": severity,
        }
    )


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
        raise ValueError("Invalid conversation support JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("Conversation support response must be a JSON object")
    return parsed

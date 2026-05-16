from __future__ import annotations

import json
import logging
import re
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field

from app.infra.contracts import LLMBase, Message
from app.modules.sessions.schemas.lesson import LessonHintRead
from app.modules.sessions.schemas.session import RealtimeCorrectionResponse
from app.modules.sessions.services.conversation_prompts import (
    build_dialogue_system_prompt,
    build_full_assessment_prompt,
    build_hint_prompt,
    build_realtime_correction_prompt,
    build_summary_prompt,
)

logger = logging.getLogger(__name__)

SESSION_END_MARKER_RE = re.compile(r"^\s*\[\[SESSION_END=(yes|no)\]\][ \t]*(?:\r?\n)?", re.IGNORECASE)
SESSION_END_MARKER_PREFIX = "[[SESSION_END="
SESSION_END_MARKER_MAX_CHARS = 80


class ConversationSupportJSONError(ValueError):
    def __init__(self, message: str, *, raw: str):
        super().__init__(message)
        self.raw = raw


class HintPayload(BaseModel):
    hint1: str = ""
    hint2: str = ""
    hint3: str = ""


class CorrectionPayload(BaseModel):
    is_good: bool = True
    better_answer: str | None = None


class SummaryPayload(BaseModel):
    summary: str = ""


class FinalEvaluationPayload(BaseModel):
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


class EndAwareReplyStream:
    def __init__(self, chunks: AsyncIterator[str]):
        self._chunks = chunks
        self.should_end = False

    def __aiter__(self) -> AsyncIterator[str]:
        return self._iter_clean_chunks()

    async def _iter_clean_chunks(self) -> AsyncIterator[str]:
        buffer = ""
        marker_checked = False

        async for chunk in self._chunks:
            if marker_checked:
                yield chunk
                continue

            buffer += chunk
            match = SESSION_END_MARKER_RE.match(buffer)
            if match:
                self.should_end = match.group(1).lower() == "yes"
                marker_checked = True
                remainder = buffer[match.end():]
                if remainder:
                    yield remainder
                continue

            normalized_buffer = buffer.lstrip()
            marker_prefix = SESSION_END_MARKER_PREFIX[: len(normalized_buffer)]
            may_still_be_marker = bool(normalized_buffer) and marker_prefix.lower() == normalized_buffer.lower()
            should_wait = (
                not normalized_buffer
                or (may_still_be_marker and len(buffer) < SESSION_END_MARKER_MAX_CHARS)
                or (normalized_buffer.upper().startswith(SESSION_END_MARKER_PREFIX) and "]]" not in normalized_buffer)
            )
            if should_wait and "\n" not in buffer and "\r" not in buffer:
                continue

            marker_checked = True
            yield buffer

        if buffer and not marker_checked:
            yield buffer


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
        learner_profile: dict[str, Any] | None = None,
    ) -> str:
        system_prompt = self._system_prompt(
            session=session,
            learner_profile=learner_profile,
            extra_instruction=(
                "Start the role-play with a brief, natural first assistant turn. "
                "Use correct, friendly, and simple English, not broken English. "
                "Use the scenario context naturally without over-explaining it. "
                "Open the conversation in character, then ask one easy question that helps the learner begin the task. "
            ),
        )
        chunks: list[str] = []
        async for chunk in self.llm.chat_stream(
            [Message(role="user", content="Please start the role-play now.")],
            system_prompt=system_prompt,
        ):
            chunks.append(chunk)
        return SESSION_END_MARKER_RE.sub("", "".join(chunks), count=1).strip()

    async def stream_reply(
        self,
        *,
        session,
        learner_profile: dict[str, Any] | None = None,
        extra_instruction: str | None = None,
    ) -> AsyncIterator[str]:
        system_prompt = self._system_prompt(
            session=session,
            learner_profile=learner_profile,
            extra_instruction=extra_instruction,
        )
        messages = session_recent_llm_messages(session, limit=self.message_limit)
        async for chunk in self.llm.chat_stream(messages, system_prompt=system_prompt):
            yield chunk

    def stream_reply_with_end_decision(
        self,
        *,
        session,
        learner_profile: dict[str, Any] | None = None,
        extra_instruction: str | None = None,
    ) -> EndAwareReplyStream:
        return EndAwareReplyStream(
            self.stream_reply(
                session=session,
                learner_profile=learner_profile,
                extra_instruction=extra_instruction,
            )
        )

    def _system_prompt(
        self,
        *,
        session,
        learner_profile: dict[str, Any] | None = None,
        extra_instruction: str | None = None,
    ) -> str:
        return build_dialogue_system_prompt(
            scenario=session.scenario,
            rolling_summary=session_rolling_summary(session),
            recent_turns=session_recent_turns_text(session, limit=self.message_limit * 2),
            learner_profile=learner_profile,
            extra_instruction=extra_instruction,
        )


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
        hints = [payload.hint1, payload.hint2, payload.hint3]
        hints = [hint.strip() for hint in hints if hint and hint.strip()]
        while len(hints) < 3:
            hints.append("Answer with one short, clear sentence.")
        return LessonHintRead(
            lesson_id=f"session-{session.id}",
            objective_id="conversation_hint",
            question=current_question,
            hints=hints[:3],
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
        try:
            payload = await _collect_json(
                self.llm,
                model=CorrectionPayload,
                system_prompt=system_prompt,
                user_text=text,
                max_tokens=self.max_tokens,
            )
        except ConversationSupportJSONError as exc:
            logger.warning(
                "Realtime correction JSON was invalid after retry; using partial fallback for scenario=%s",
                scenario_title,
            )
            payload = _fallback_correction_payload(raw=exc.raw, fallback_text=text)
        return RealtimeCorrectionResponse(
            is_good=payload.is_good,
            better_answer=(payload.better_answer or None),
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
            tasks=session.scenario.tasks or [],
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


async def _collect_json(
    llm: LLMBase,
    *,
    model: type[BaseModel],
    system_prompt: str,
    user_text: str,
    max_tokens: int,
) -> Any:
    raw = await _collect_raw_response(
        llm,
        system_prompt=system_prompt,
        user_text=user_text,
        max_tokens=max_tokens,
    )
    try:
        return model.model_validate(_parse_json_object(raw))
    except ValueError:
        logger.warning("Invalid %s JSON response on first attempt; retrying once", model.__name__)
        retry_raw = await _collect_raw_response(
            llm,
            system_prompt=_build_json_repair_system_prompt(system_prompt),
            user_text=_build_json_repair_user_text(user_text=user_text, invalid_json=raw),
            max_tokens=max_tokens,
        )
        try:
            return model.model_validate(_parse_json_object(retry_raw))
        except ValueError as retry_exc:
            raise ConversationSupportJSONError("Invalid conversation support JSON", raw=retry_raw or raw) from retry_exc


async def _collect_raw_response(
    llm: LLMBase,
    *,
    system_prompt: str,
    user_text: str,
    max_tokens: int,
) -> str:
    chunks: list[str] = []
    async for chunk in llm.chat_stream(
        [Message(role="user", content=user_text.strip())],
        system_prompt=system_prompt,
        max_tokens=max_tokens,
    ):
        chunks.append(chunk)
    return "".join(chunks)


def _sorted_messages(session) -> list[Any]:
    return sorted(session.messages or [], key=lambda item: item.order_index)


def _fallback_correction_payload(*, raw: str, fallback_text: str) -> CorrectionPayload:
    better_answer = _extract_json_string_field(raw, "better_answer")
    return CorrectionPayload(is_good=True, better_answer=better_answer)


def _extract_json_string_field(raw: str, field_name: str) -> str | None:
    match = re.search(
        rf'"{re.escape(field_name)}"\s*:\s*"((?:\\.|[^"\\])*)"',
        raw or "",
        flags=re.DOTALL,
    )
    if not match:
        return None
    try:
        return json.loads(f'"{match.group(1)}"')
    except json.JSONDecodeError:
        return None


def _build_json_repair_system_prompt(system_prompt: str) -> str:
    return "\n".join(
        [
            "Your previous answer was invalid or truncated JSON.",
            "Return only one complete valid JSON object that follows the requested schema exactly.",
            "Do not include markdown, explanations, or partial arrays/strings.",
            system_prompt,
        ]
    )


def _build_json_repair_user_text(*, user_text: str, invalid_json: str) -> str:
    return "\n".join(
        [
            "Original user text:",
            user_text.strip() or "(empty)",
            "",
            "Previous invalid JSON response:",
            invalid_json.strip() or "(empty)",
            "",
            "Rewrite it as one complete valid JSON object.",
        ]
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

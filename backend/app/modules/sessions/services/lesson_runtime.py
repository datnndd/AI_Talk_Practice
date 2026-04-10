from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import BadRequestError
from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.schemas.lesson import (
    LessonHintRead,
    LessonHintSeed,
    LessonObjective,
    LessonObjectiveState,
    LessonPackage,
    LessonProgressState,
    LessonProgressSummary,
    LessonStateRead,
)

STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "be",
    "can",
    "for",
    "from",
    "get",
    "have",
    "how",
    "i",
    "in",
    "is",
    "it",
    "like",
    "of",
    "on",
    "or",
    "the",
    "to",
    "we",
    "what",
    "would",
    "you",
    "your",
}

WORD_RE = re.compile(r"[a-zA-Z']+")


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if any(separator in text for separator in [";", "\n", "|"]):
            parts = re.split(r"[;\n|]+", text)
            return [part.strip() for part in parts if part.strip()]
        return [text]
    return [str(value).strip()]


def _normalize_text(text: str) -> str:
    lowered = text.lower()
    return " ".join(WORD_RE.findall(lowered))


def _keyword_tokens(text: str) -> list[str]:
    return [token for token in WORD_RE.findall(text.lower()) if len(token) > 2 and token not in STOPWORDS]


def _title_case_topic(scenario: Scenario) -> str:
    metadata = scenario.scenario_metadata or {}
    return (
        str(metadata.get("topic") or metadata.get("conversation_topic") or scenario.title or "Conversation")
        .strip()
    )


def _assigned_task(scenario: Scenario) -> str:
    metadata = scenario.scenario_metadata or {}
    return (
        str(
            metadata.get("assigned_task")
            or metadata.get("task")
            or metadata.get("user_goal")
            or metadata.get("goal")
            or scenario.description
            or f"Talk about {scenario.title}"
        ).strip()
    )


def _persona(scenario: Scenario) -> str:
    metadata = scenario.scenario_metadata or {}
    return str(metadata.get("persona") or metadata.get("partner_persona") or "Friendly speaking partner").strip()


def _max_follow_ups_for_level(level: str) -> int:
    normalized = (level or "").lower()
    if normalized in {"beginner", "easy", "a1", "a2"}:
        return 2
    if normalized in {"intermediate", "b1", "b2", "medium"}:
        return 2
    return 3


def _min_words_for_level(level: str) -> int:
    normalized = (level or "").lower()
    if normalized in {"beginner", "easy", "a1", "a2"}:
        return 4
    if normalized in {"intermediate", "b1", "b2", "medium"}:
        return 6
    return 8


def _goal_points(goal: str) -> list[str]:
    text = re.sub(r"\([^)]*\)", "", goal)
    parts = re.split(r",|/| and |\+", text, flags=re.IGNORECASE)
    cleaned = [part.strip(" .:-") for part in parts if part.strip(" .:-")]
    if cleaned:
        return cleaned[:3]
    return [goal.strip()]


def _build_objective_questions(
    *,
    index: int,
    goal: str,
    topic: str,
    assigned_task: str,
    expected_points: list[str],
) -> tuple[str, list[str]]:
    if index == 0:
        main_question = f"{assigned_task} What would you say first?"
    else:
        main_question = f"Now focus on {goal.lower()}. How would you continue the conversation?"

    follow_ups = []
    for point in expected_points[:2]:
        follow_ups.append(f"Can you also mention {point.lower()}?")
    follow_ups.append(f"How would you say that naturally in this {topic.lower()} situation?")
    return main_question, follow_ups[:3]


def chunk_text_for_stream(text: str, chunk_size: int = 48) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > chunk_size:
            chunks.append(f"{current} ")
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks


@dataclass
class LessonAdvanceResult:
    assistant_text: str
    state: LessonStateRead


class LessonRuntimeService:
    @classmethod
    def ensure_session_lesson(
        cls,
        *,
        scenario: Scenario,
        session_metadata: dict[str, Any] | None,
        level: str | None,
        regenerate: bool = False,
    ) -> tuple[LessonPackage, LessonProgressState, dict[str, Any]]:
        existing_metadata = dict(session_metadata or {})
        if not regenerate and cls.has_lesson(existing_metadata):
            return cls.deserialize_lesson_metadata(existing_metadata)

        package = cls.create_lesson_package(scenario=scenario, level=level)
        state = cls.initial_state(package)
        hints: dict[str, Any] = {}
        return package, state, hints

    @staticmethod
    def create_lesson_package(
        *,
        scenario: Scenario,
        level: str | None,
    ) -> LessonPackage:
        objectives_source = _normalize_list(scenario.learning_objectives)
        if not objectives_source:
            objectives_source = [scenario.description or scenario.title]

        topic = _title_case_topic(scenario)
        assigned_task = _assigned_task(scenario)
        resolved_level = (level or "intermediate").strip()
        objectives: list[LessonObjective] = []

        for index, goal in enumerate(objectives_source[:4]):
            expected_points = _goal_points(goal)
            main_question, follow_ups = _build_objective_questions(
                index=index,
                goal=goal,
                topic=topic,
                assigned_task=assigned_task,
                expected_points=expected_points,
            )
            objectives.append(
                LessonObjective(
                    objective_id=f"obj_{index + 1}",
                    goal=goal,
                    main_question=main_question,
                    follow_up_questions=follow_ups,
                    expected_points=expected_points,
                    hint_seed=LessonHintSeed(
                        focus=goal,
                        grammar="Use short spoken English sentences and answer directly.",
                        max_length=2 if resolved_level.lower() in {"beginner", "easy", "a1", "a2"} else 4,
                    ),
                )
            )

        return LessonPackage(
            lesson_id=str(uuid.uuid4()),
            scenario_id=scenario.id,
            scenario=topic,
            level=resolved_level,
            persona=_persona(scenario),
            objectives=objectives,
        )

    @staticmethod
    def initial_state(package: LessonPackage) -> LessonProgressState:
        if not package.objectives:
            raise BadRequestError("Lesson package has no objectives")

        return LessonProgressState(
            current_objective_index=0,
            last_question=package.objectives[0].main_question,
        )

    @staticmethod
    def serialize_lesson_metadata(
        *,
        package: LessonPackage,
        state: LessonProgressState,
        hints: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "version": "lesson_v1",
            "package": package.model_dump(),
            "state": state.model_dump(),
            "hints": hints or {},
        }

    @staticmethod
    def deserialize_lesson_metadata(metadata: dict[str, Any] | None) -> tuple[LessonPackage, LessonProgressState, dict[str, Any]]:
        lesson = (metadata or {}).get("lesson") or {}
        package = LessonPackage.model_validate(lesson.get("package") or {})
        state = LessonProgressState.model_validate(lesson.get("state") or {})
        hints = lesson.get("hints") or {}
        return package, state, hints

    @staticmethod
    def has_lesson(metadata: dict[str, Any] | None) -> bool:
        lesson = (metadata or {}).get("lesson") or {}
        return bool(lesson.get("package") and lesson.get("state"))

    @staticmethod
    def build_state_read(
        *,
        session_id: int,
        scenario: Scenario,
        package: LessonPackage,
        state: LessonProgressState,
        matched_points: list[str] | None = None,
        missing_points: list[str] | None = None,
    ) -> LessonStateRead:
        objectives = package.objectives
        current_index = min(state.current_objective_index, max(len(objectives) - 1, 0))
        current = objectives[current_index]
        objective_id = current.objective_id
        turns_taken = state.attempts_by_objective.get(objective_id, 0)
        follow_up_index = state.follow_up_index_by_objective.get(objective_id, 0)
        remaining = max(0, _max_follow_ups_for_level(package.level) - follow_up_index)
        completed = len(state.completed_objective_ids)
        total = len(objectives)
        progress = LessonProgressSummary(
            completed=completed,
            total=total,
            percent=int((completed / total) * 100) if total else 100,
        )
        suggested = [f"I would mention {point.lower()}." for point in (missing_points or current.expected_points[:2])][:3]

        return LessonStateRead(
            lesson_id=package.lesson_id,
            session_id=session_id,
            scenario_id=package.scenario_id,
            topic=_title_case_topic(scenario),
            assigned_task=_assigned_task(scenario),
            persona=package.persona,
            status=state.status,
            current_question=state.last_question or current.main_question,
            current_objective=LessonObjectiveState(
                objective_id=current.objective_id,
                goal=current.goal,
                main_question=current.main_question,
                expected_points=current.expected_points,
                matched_points=matched_points or [],
                missing_points=missing_points or list(current.expected_points),
                turns_taken=turns_taken,
                remaining_follow_ups=remaining,
                status="completed" if current.objective_id in state.completed_objective_ids else "active",
            ),
            progress=progress,
            should_end=state.should_end,
            end_reason=state.end_reason,
            completion_message=state.completion_message,
            suggested_responses=suggested,
        )

    @staticmethod
    def _match_expected_points(answer: str, expected_points: list[str]) -> tuple[list[str], list[str]]:
        normalized_answer = _normalize_text(answer)
        answer_tokens = set(_keyword_tokens(answer))
        matched: list[str] = []

        for point in expected_points:
            normalized_point = _normalize_text(point)
            point_tokens = [token for token in _keyword_tokens(point) if token]
            if normalized_point and normalized_point in normalized_answer:
                matched.append(point)
                continue
            if point_tokens and any(token in answer_tokens for token in point_tokens):
                matched.append(point)

        missing = [point for point in expected_points if point not in matched]
        return matched, missing

    @classmethod
    def advance(
        cls,
        *,
        scenario: Scenario,
        session_id: int,
        package: LessonPackage,
        state: LessonProgressState,
        user_answer: str,
    ) -> LessonAdvanceResult:
        if state.status == "completed":
            return LessonAdvanceResult(
                assistant_text=state.completion_message or "This conversation is already complete.",
                state=cls.build_state_read(
                    session_id=session_id,
                    scenario=scenario,
                    package=package,
                    state=state,
                ),
            )

        current = package.objectives[state.current_objective_index]
        objective_id = current.objective_id
        attempts = state.attempts_by_objective.get(objective_id, 0) + 1
        state.attempts_by_objective[objective_id] = attempts

        matched, missing = cls._match_expected_points(user_answer, current.expected_points)
        word_count = len(_keyword_tokens(user_answer))
        max_follow_ups = _max_follow_ups_for_level(package.level)
        min_words = _min_words_for_level(package.level)
        follow_up_index = state.follow_up_index_by_objective.get(objective_id, 0)

        enough_content = word_count >= min_words
        enough_coverage = len(matched) >= max(1, (len(current.expected_points) + 1) // 2)
        objective_complete = enough_content and (enough_coverage or follow_up_index >= max_follow_ups)

        if objective_complete:
            if objective_id not in state.completed_objective_ids:
                state.completed_objective_ids.append(objective_id)

            if state.current_objective_index >= len(package.objectives) - 1:
                state.status = "completed"
                state.should_end = True
                state.end_reason = "all_objectives_completed"
                state.completion_message = (
                    f"You covered the main goals for {package.scenario.lower()}. Wrap up the conversation politely."
                )
                state.last_question = state.completion_message
                return LessonAdvanceResult(
                    assistant_text=state.completion_message,
                    state=cls.build_state_read(
                        session_id=session_id,
                        scenario=scenario,
                        package=package,
                        state=state,
                        matched_points=matched,
                        missing_points=missing,
                    ),
                )

            state.current_objective_index += 1
            next_objective = package.objectives[state.current_objective_index]
            state.last_question = next_objective.main_question
            return LessonAdvanceResult(
                assistant_text=next_objective.main_question,
                state=cls.build_state_read(
                    session_id=session_id,
                    scenario=scenario,
                    package=package,
                    state=state,
                ),
            )

        if missing:
            next_question = f"Good start. Can you also mention {missing[0].lower()}?"
        elif follow_up_index < len(current.follow_up_questions):
            next_question = current.follow_up_questions[follow_up_index]
        else:
            next_question = f"Add one more clear detail about {current.goal.lower()}."

        state.follow_up_index_by_objective[objective_id] = follow_up_index + 1
        state.last_question = next_question

        return LessonAdvanceResult(
            assistant_text=next_question,
            state=cls.build_state_read(
                session_id=session_id,
                scenario=scenario,
                package=package,
                state=state,
                matched_points=matched,
                missing_points=missing,
            ),
        )

    @classmethod
    def build_hint(
        cls,
        *,
        package: LessonPackage,
        state: LessonProgressState,
        user_last_answer: str | None,
        cached: bool = False,
    ) -> LessonHintRead:
        current = package.objectives[state.current_objective_index]
        answer = (user_last_answer or "").strip()
        matched, missing = cls._match_expected_points(answer, current.expected_points) if answer else ([], list(current.expected_points))
        keywords = missing or current.expected_points[:3]
        max_length = current.hint_seed.max_length
        keyword_phrase = ", ".join(item.lower() for item in keywords[:3])

        if answer:
            analysis = (
                f"Ban da noi duoc {len(matched)}/{len(current.expected_points)} y chinh. "
                f"Can bo sung: {', '.join(item.lower() for item in missing[:3]) or 'mot chi tiet cu the hon'}."
            )
        else:
            analysis = "Ban chua tra loi ro y chinh. Hay noi 1-2 cau ngan, di thang vao muc tieu hien tai."

        answer_strategy = (
            f"Tra loi toi da {max_length} cau. Noi truc tiep ve {current.goal.lower()}, "
            f"sau do chen cac tu khoa: {keyword_phrase or current.goal.lower()}."
        )
        sample_answer = (
            f"In this situation, I would focus on {current.goal.lower()}. "
            f"I would mention {keyword_phrase or current.goal.lower()} clearly."
        )
        sample_answer_easy = (
            f"I would talk about {current.goal.lower()}. "
            f"I would say {keyword_phrase or current.goal.lower()}."
        )

        return LessonHintRead(
            lesson_id=package.lesson_id,
            objective_id=current.objective_id,
            analysis_vi=analysis,
            answer_strategy_vi=answer_strategy,
            keywords=keywords[:4],
            sample_answer=sample_answer,
            sample_answer_easy=sample_answer_easy,
            cached=cached,
            metadata={
                "matched_points": matched,
                "missing_points": missing,
                "focus": current.hint_seed.focus,
            },
        )

    @staticmethod
    def store_hint(
        *,
        hints: dict[str, Any],
        objective_id: str,
        answer: str | None,
        payload: LessonHintRead,
    ) -> dict[str, Any]:
        key = f"{objective_id}:{_normalize_text(answer or '')}"
        updated = dict(hints)
        updated[key] = payload.model_dump()
        return updated

    @staticmethod
    def get_cached_hint(
        *,
        hints: dict[str, Any],
        objective_id: str,
        answer: str | None,
    ) -> LessonHintRead | None:
        key = f"{objective_id}:{_normalize_text(answer or '')}"
        cached = hints.get(key)
        if not cached:
            return None
        return LessonHintRead.model_validate(cached)

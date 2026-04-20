from __future__ import annotations

import logging
import re
import uuid
from dataclasses import dataclass
from typing import Any

from app.core.exceptions import BadRequestError, UpstreamServiceError
from app.infra.contracts import LLMBase, Message
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
from app.modules.sessions.services.lesson_prompts import (
    LESSON_HINT_SYSTEM_PROMPT,
    LESSON_PLAN_SYSTEM_PROMPT,
    build_lesson_hint_user_prompt,
    build_lesson_plan_user_prompt,
    parse_lesson_hint_response,
    parse_lesson_plan_response,
)

logger = logging.getLogger(__name__)

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
    """
    Returns the situation/detail description provided by the admin.
    This is what the AI uses to understand the context.
    """
    return (scenario.description or scenario.title or "General conversation practice").strip()


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


META_OPENING_FRAGMENTS = (
    "practice ",
    "i will start",
    "what would you say first",
    "your task is",
    "you are in a scenario",
    "selected scenario",
    "lesson goal",
    "conversation goal",
    "objective",
    "roleplay",
)


def _is_meta_opening(text: str) -> bool:
    normalized = _normalize_text(text)
    return any(fragment in normalized for fragment in META_OPENING_FRAGMENTS)


def _metadata_opening(scenario: Scenario) -> str:
    metadata = scenario.scenario_metadata or {}
    for key in ("opening_message", "opening_line", "initial_message", "first_message", "start_message"):
        value = metadata.get(key)
        if isinstance(value, str) and value.strip() and not _is_meta_opening(value):
            return value.strip()
    return ""


def _fallback_opening_message(*, scenario: Scenario, topic: str) -> str:
    configured = _metadata_opening(scenario)
    if configured:
        return configured

    persona = _persona(scenario)
    if persona and persona.lower() != "friendly speaking partner":
        return "Hello! How can I help you today?"

    return "Hello! I'm ready to start our conversation whenever you are. What would you like to say first?"


def _build_objective_questions(
    *,
    index: int,
    goal: str,
    scenario: Scenario,
    topic: str,
    expected_points: list[str],
) -> tuple[str, list[str]]:
    if index == 0:
        main_question = _fallback_opening_message(scenario=scenario, topic=topic)
    else:
        main_question = "Could you tell me a little more about that?"

    follow_ups = []
    for point in expected_points[:2]:
        follow_ups.append("Could you give me a specific detail or an example to explain that further?")
    follow_ups.append("How would you express that naturally in a real-life situation?")
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


class LessonPlanGenerationError(UpstreamServiceError):
    code = "lesson_plan_generation_failed"


@dataclass(frozen=True)
class ObjectiveBlueprint:
    goal: str
    expected_points: list[str]
    main_question: str
    follow_up_questions: list[str]
    vocabulary: list[str]


def _level_band(level: str | None) -> str:
    normalized = (level or "").lower()
    if normalized in {"beginner", "easy", "a1", "a2"}:
        return "beginner"
    if normalized in {"advanced", "hard", "c1", "c2"}:
        return "advanced"
    return "intermediate"


def _objective_count_for_level(level: str | None, available: int) -> int:
    band = _level_band(level)
    desired = {"beginner": 2, "intermediate": 3, "advanced": 4}[band]
    return max(1, min(desired, available))


def _fallback_expected_points(goal: str) -> list[str]:
    points = _goal_points(goal)
    if points and _normalize_text(points[0]) != _normalize_text(goal):
        return points[:3]
    tokens = _keyword_tokens(goal)
    if len(tokens) >= 3:
        return [" ".join(tokens[:3])]
    return [goal.strip() or "a specific detail"]


def _context_keywords(*values: str, limit: int = 4) -> list[str]:
    text = " ".join(value for value in values if value)
    tokens = _keyword_tokens(text)
    keywords: list[str] = []
    for index, token in enumerate(tokens):
        if token in keywords:
            continue
        next_token = tokens[index + 1] if index + 1 < len(tokens) else ""
        if next_token and next_token not in STOPWORDS and next_token != token:
            phrase = f"{token} {next_token}"
        else:
            phrase = token
        if phrase not in keywords:
            keywords.append(phrase)
        if len(keywords) >= limit:
            break
    return keywords


def _fallback_goal_context(
    *,
    goal: str,
    scenario: Scenario,
    topic: str,
    assigned_task: str,
) -> tuple[str, list[str]]:
    normalized_goal = _normalize_text(goal)
    context_points = _context_keywords(
        topic,
        assigned_task,
        scenario.description or "",
        scenario.ai_system_prompt or "",
        limit=4,
    )

    if "vocabulary" in normalized_goal or "word" in normalized_goal or "phrase" in normalized_goal:
        return (
            f"Use precise phrases for {topic}",
            context_points or [topic],
        )

    return goal, _fallback_expected_points(goal)


def _fallback_blueprints(
    *,
    scenario: Scenario,
    topic: str,
    assigned_task: str,
    level: str | None,
) -> list[ObjectiveBlueprint]:
    # Strictly use admin defined objectives. 
    # If none are provided, the goal is just the scenario itself.
    goals = _normalize_list(scenario.learning_objectives)
    if not goals:
        goals = ["Hoàn thành cuộc hội thoại dựa trên tình huống"]

    count = _objective_count_for_level(level, len(goals))
    blueprints: list[ObjectiveBlueprint] = []
    for index, goal in enumerate(goals[:count]):
        resolved_goal, expected_points = _fallback_goal_context(
            goal=goal,
            scenario=scenario,
            topic=topic,
            assigned_task=assigned_task,
        )
        main_question, follow_ups = _build_objective_questions(
            index=index,
            goal=resolved_goal,
            scenario=scenario,
            topic=topic,
            expected_points=expected_points,
        )
        blueprints.append(
            ObjectiveBlueprint(
                goal=resolved_goal,
                expected_points=expected_points,
                main_question=main_question,
                follow_up_questions=follow_ups,
                vocabulary=expected_points,
            )
        )
    return blueprints


def _normalize_string_list(value: Any, *, limit: int = 4) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()][:limit]
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    return []


def _question_for_missing_point(current: LessonObjective, missing_point: str) -> str:
    point = missing_point.lower()
    goal = current.goal.lower()
    examples = ", ".join(current.hint_seed.grammar.split(", ")[:2]) if current.hint_seed.grammar else point
    return (
        f"Could you add one concrete detail about {point}? "
        f"For example, use a phrase like {examples} while you answer about {goal}."
    )


def _build_completion_message(
    *,
    package: LessonPackage,
    state: LessonProgressState,
    matched_points: list[str],
    missing_points: list[str],
) -> str:
    achieved = [
        objective.goal
        for objective in package.objectives
        if objective.objective_id in state.completed_objective_ids
    ]
    remaining = [
        objective.goal
        for objective in package.objectives
        if objective.objective_id not in state.completed_objective_ids
    ]
    strengths = matched_points[:2] or ["clear participation", "staying on topic"]
    improvements = missing_points[:2] or remaining[:2] or ["add more specific examples", "use more precise vocabulary"]

    achieved_text = "; ".join(achieved) if achieved else "the main conversation task"
    strengths_text = "; ".join(strengths)
    improvements_text = "; ".join(improvements)
    return (
        "Session summary: "
        f"Goals achieved: {achieved_text}. "
        f"Strengths: {strengths_text}. "
        f"Improve next: {improvements_text}. "
        f"Overall: you completed this {package.scenario.lower()} practice round at {package.level} level."
    )


def _sample_answer_for_objective(current: LessonObjective, keywords: list[str], *, easy: bool = False) -> str:
    primary = (keywords[0] if keywords else current.goal).lower()
    secondary = (keywords[1] if len(keywords) > 1 else primary).lower()
    if easy:
        return f"I want to mention {primary}."
    return f"I would mention {primary}, then add a specific detail about {secondary}."


def _hint_question(current: LessonObjective, state: LessonProgressState) -> str:
    return (state.last_question or current.main_question or "").strip()


def _hint_vocabulary(current: LessonObjective) -> list[str]:
    vocabulary = [
        part.strip()
        for part in re.split(r",|;|\n|\|", current.hint_seed.grammar or "")
        if part.strip()
    ]
    return vocabulary or current.expected_points[:4] or [current.goal]


class LessonRuntimeService:
    @classmethod
    async def ensure_session_lesson_dynamic(
        cls,
        *,
        scenario: Scenario,
        session_metadata: dict[str, Any] | None,
        level: str | None,
        llm: LLMBase | None = None,
        regenerate: bool = False,
    ) -> tuple[LessonPackage, LessonProgressState, dict[str, Any]]:
        # Delegated directly to static ensuring logic. Dynamic generation is deprecated.
        return cls.ensure_session_lesson(
            scenario=scenario,
            session_metadata=session_metadata,
            level=level,
            regenerate=regenerate,
        )

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

    @classmethod
    async def create_lesson_package_dynamic(
        cls,
        *,
        scenario: Scenario,
        level: str | None,
        llm: LLMBase | None,
    ) -> LessonPackage:
        # The AI-generated lesson dynamic process is deleted. Uses static definitions.
        return cls.create_lesson_package(scenario=scenario, level=level)

    @staticmethod
    def _lesson_plan_max_tokens(llm: LLMBase) -> int:
        config = getattr(llm, "_config", None)
        return int(getattr(config, "lesson_plan_llm_max_tokens", 2400))

    @staticmethod
    def _lesson_hint_max_tokens(llm: LLMBase) -> int:
        config = getattr(llm, "_config", None)
        return int(getattr(config, "lesson_hint_llm_max_tokens", 700))

    @staticmethod
    def create_lesson_package(
        *,
        scenario: Scenario,
        level: str | None,
    ) -> LessonPackage:
        topic = _title_case_topic(scenario)
        assigned_task = _assigned_task(scenario)
        resolved_level = (level or "intermediate").strip()
        blueprints = _fallback_blueprints(
            scenario=scenario,
            level=resolved_level,
            topic=topic,
            assigned_task=assigned_task,
        )
        return LessonRuntimeService._package_from_blueprints(
            scenario=scenario,
            topic=topic,
            level=resolved_level,
            blueprints=blueprints,
        )

    @staticmethod
    def create_lesson_package_from_plan(
        *,
        scenario: Scenario,
        level: str | None,
        plan: dict[str, Any],
        strict: bool = False,
    ) -> LessonPackage:
        topic = _title_case_topic(scenario)
        assigned_task = _assigned_task(scenario)
        resolved_level = (level or "intermediate").strip()
        goals = plan.get("goals")
        if not isinstance(goals, list):
            if strict:
                raise LessonPlanGenerationError("The AI lesson plan did not include a valid goals list.")
            return LessonRuntimeService.create_lesson_package(scenario=scenario, level=resolved_level)

        opening = str(plan.get("opening_message") or "").strip()
        if opening and _is_meta_opening(opening) and strict:
            raise LessonPlanGenerationError("The AI lesson plan opening was not a valid roleplay line.")
        elif opening and _is_meta_opening(opening):
            opening = _fallback_opening_message(scenario=scenario, topic=topic)
        blueprints: list[ObjectiveBlueprint] = []
        goal_limit = _objective_count_for_level(resolved_level, len(goals))
        for index, item in enumerate(goals[:goal_limit]):
            if not isinstance(item, dict):
                continue
            goal = str(item.get("goal") or "").strip()
            if not goal:
                continue
            expected_points = _normalize_string_list(
                item.get("success_criteria") or item.get("expected_points"),
                limit=4,
            ) or _fallback_expected_points(goal)
            vocabulary = _normalize_string_list(
                item.get("useful_phrases") or item.get("vocabulary"),
                limit=6,
            ) or expected_points
            follow_ups = _normalize_string_list(item.get("follow_up_questions"), limit=3)
            question = str(item.get("question") or item.get("main_question") or item.get("starting_question") or "").strip()
            if question and _is_meta_opening(question):
                question = ""
            main_question = opening if index == 0 and opening else question
            if not main_question:
                main_question, default_follow_ups = _build_objective_questions(
                    index=index,
                    goal=goal,
                    scenario=scenario,
                    topic=topic,
                    expected_points=expected_points,
                )
                follow_ups = follow_ups or default_follow_ups
            blueprints.append(
                ObjectiveBlueprint(
                    goal=goal,
                    expected_points=expected_points,
                    main_question=main_question,
                    follow_up_questions=follow_ups,
                    vocabulary=vocabulary,
                )
            )

        if not blueprints:
            if strict:
                raise LessonPlanGenerationError("The AI lesson plan did not include any usable conversation goals.")
            return LessonRuntimeService.create_lesson_package(scenario=scenario, level=resolved_level)

        return LessonRuntimeService._package_from_blueprints(
            scenario=scenario,
            topic=topic,
            level=resolved_level,
            blueprints=blueprints,
        )

    @staticmethod
    def _package_from_blueprints(
        *,
        scenario: Scenario,
        topic: str,
        level: str,
        blueprints: list[ObjectiveBlueprint],
    ) -> LessonPackage:
        objectives: list[LessonObjective] = []

        for index, blueprint in enumerate(blueprints):
            objectives.append(
                LessonObjective(
                    objective_id=f"obj_{index + 1}",
                    goal=blueprint.goal,
                    main_question=blueprint.main_question,
                    follow_up_questions=blueprint.follow_up_questions,
                    expected_points=blueprint.expected_points,
                    hint_seed=LessonHintSeed(
                        focus=blueprint.goal,
                        grammar=", ".join(blueprint.vocabulary),
                        max_length=2 if level.lower() in {"beginner", "easy", "a1", "a2"} else 4,
                    ),
                )
            )

        return LessonPackage(
            lesson_id=str(uuid.uuid4()),
            scenario_id=scenario.id,
            scenario=topic,
            level=level,
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
        suggested = [
            _sample_answer_for_objective(current, [point], easy=True)
            for point in (missing_points or current.expected_points[:2])
        ][:3]

        return LessonStateRead(
            lesson_id=package.lesson_id,
            session_id=session_id,
            scenario_id=package.scenario_id,
            topic=_title_case_topic(scenario),
            assigned_task=_assigned_task(scenario),
            persona=package.persona,
            lesson_goals=[objective.goal for objective in objectives],
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
                state.completion_message = _build_completion_message(
                    package=package,
                    state=state,
                    matched_points=matched,
                    missing_points=missing,
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

        if follow_up_index < len(current.follow_up_questions):
            next_question = current.follow_up_questions[follow_up_index]
        elif missing:
            next_question = _question_for_missing_point(current, missing[0])
        else:
            next_question = f"Could you add one more real example about {current.goal.lower()}?"

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
        objective_id = current.objective_id
        follow_up_index = state.follow_up_index_by_objective.get(objective_id, 0)
        question = _hint_question(current, state)
        keywords = _hint_vocabulary(current)[:4]
        max_length = current.hint_seed.max_length
        keyword_phrase = ", ".join(item.lower() for item in keywords[:3])

        analysis = (
            f"AI dang hoi: \"{question}\". "
            f"Trong tam la {current.goal.lower()}, nen tra loi dung vao y chinh cua cau hoi."
        )

        # Adjust advice based on how many follow-ups have already been used
        if follow_up_index == 0:
            strategy_prefix = f"Tra loi toi da {max_length} cau."
        else:
            strategy_prefix = f"Lan nay hay thu dung cac tu khoa sau va tra loi trong {max_length} cau."

        answer_strategy = (
            f"{strategy_prefix} Noi truc tiep ve {current.goal.lower()}, "
            f"sau do chen cac tu khoa: {keyword_phrase or current.goal.lower()}."
        )

        sample_answer = _sample_answer_for_objective(current, keywords, easy=False)
        sample_answer_easy = _sample_answer_for_objective(current, keywords, easy=True)

        return LessonHintRead(
            lesson_id=package.lesson_id,
            objective_id=current.objective_id,
            question=question,
            analysis_vi=analysis,
            answer_strategy_vi=answer_strategy,
            keywords=keywords[:4],
            sample_answers=[sample_answer, sample_answer_easy],
            sample_answer=sample_answer,
            sample_answer_easy=sample_answer_easy,
            cached=cached,
            metadata={
                "focus": current.hint_seed.focus,
                "follow_up_index": follow_up_index,
                "source": "fallback",
            },
        )

    @classmethod
    async def build_hint_dynamic(
        cls,
        *,
        scenario: Scenario,
        package: LessonPackage,
        state: LessonProgressState,
        llm: LLMBase,
    ) -> LessonHintRead:
        current = package.objectives[state.current_objective_index]
        question = _hint_question(current, state)
        vocabulary = _hint_vocabulary(current)
        prompt = build_lesson_hint_user_prompt(
            scenario=scenario,
            persona=package.persona,
            level=package.level,
            current_question=question,
            goal=current.goal,
            expected_points=current.expected_points,
            useful_vocabulary=vocabulary,
        )

        chunks: list[str] = []
        async for chunk in llm.chat_stream(
            [Message(role="user", content=prompt)],
            system_prompt=LESSON_HINT_SYSTEM_PROMPT,
            max_tokens=cls._lesson_hint_max_tokens(llm),
        ):
            chunks.append(chunk)

        payload = parse_lesson_hint_response("".join(chunks))
        if not payload:
            raise ValueError("LLM returned an invalid lesson hint payload")

        return cls.create_hint_from_plan(
            package=package,
            state=state,
            payload=payload,
        )

    @classmethod
    def create_hint_from_plan(
        cls,
        *,
        package: LessonPackage,
        state: LessonProgressState,
        payload: dict[str, Any],
        cached: bool = False,
    ) -> LessonHintRead:
        current = package.objectives[state.current_objective_index]
        objective_id = current.objective_id
        follow_up_index = state.follow_up_index_by_objective.get(objective_id, 0)
        question = _hint_question(current, state)

        analysis = str(payload.get("question_analysis_vi") or payload.get("analysis_vi") or "").strip()
        strategy = str(payload.get("answer_strategy_vi") or "").strip()
        keywords = _normalize_string_list(payload.get("keywords"), limit=6) or _hint_vocabulary(current)[:4]
        sample_answers = _normalize_string_list(payload.get("sample_answers"), limit=3)
        if not sample_answers:
            sample_answers = _normalize_string_list(payload.get("sample_answer"), limit=1)

        simple_answer = str(
            payload.get("simple_answer")
            or payload.get("sample_answer_easy")
            or ""
        ).strip()
        if not sample_answers and simple_answer:
            sample_answers = [simple_answer]

        sample_answer = sample_answers[0] if sample_answers else ""
        sample_answer_easy = simple_answer or (sample_answers[-1] if sample_answers else "")

        if not analysis or not strategy or not sample_answer:
            raise ValueError("LLM lesson hint payload is missing required fields")

        return LessonHintRead(
            lesson_id=package.lesson_id,
            objective_id=objective_id,
            question=question,
            analysis_vi=analysis,
            answer_strategy_vi=strategy,
            keywords=keywords[:6],
            sample_answers=sample_answers[:3],
            sample_answer=sample_answer,
            sample_answer_easy=sample_answer_easy,
            cached=cached,
            metadata={
                "focus": current.hint_seed.focus,
                "follow_up_index": follow_up_index,
                "source": "llm",
            },
        )

    @staticmethod
    def store_hint(
        *,
        hints: dict[str, Any],
        objective_id: str,
        question: str | None,
        payload: LessonHintRead,
        follow_up_index: int = 0,
    ) -> dict[str, Any]:
        key = f"{objective_id}:{follow_up_index}:{_normalize_text(question or '')}"
        updated = dict(hints)
        updated[key] = payload.model_dump()
        return updated

    @staticmethod
    def get_cached_hint(
        *,
        hints: dict[str, Any],
        objective_id: str,
        question: str | None,
        follow_up_index: int = 0,
    ) -> LessonHintRead | None:
        key = f"{objective_id}:{follow_up_index}:{_normalize_text(question or '')}"
        cached = hints.get(key)
        if not cached:
            return None
        return LessonHintRead.model_validate(cached)

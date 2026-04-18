from __future__ import annotations

import json
import re
from typing import Any

from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.services.hybrid_conversation.schemas import ScenarioDefinition, ScenarioPhase


def build_scenario_definition(
    scenario: Scenario,
    *,
    variation_prompt: str | None = None,
    user_level: str | None = None,
) -> ScenarioDefinition:
    metadata = dict(scenario.scenario_metadata or {})
    objectives = _listify(scenario.learning_objectives)
    target_skills = _listify(scenario.target_skills)
    tags = _listify(scenario.tags)
    target_vocabulary = _listify(metadata.get("target_vocabulary") or metadata.get("vocab_focus"))
    target_functions = _listify(metadata.get("target_functions") or metadata.get("language_functions"))

    # Derive the overall objective from learning objectives first, then description
    objective = _first_text(
        "; ".join(objectives) if objectives else "",
        scenario.description,
        "General conversation practice",
    )

    # AI role: prefer explicit metadata keys, then parse from system prompt, then generic
    ai_role = _first_text(
        metadata.get("ai_role"),
        metadata.get("persona"),
        metadata.get("partner_persona"),
        _role_from_prompt(scenario.ai_system_prompt),
        "Conversation partner",
    )
    user_role = _first_text(metadata.get("user_role"), metadata.get("learner_role"), "Learner")

    # Build phases strictly from learning objectives
    phases = _build_phases_from_objectives(objectives, scenario_title=scenario.title)

    opening = _first_text(
        scenario.opening_message,
        metadata.get("opening_message"),
        metadata.get("opening_line"),
        metadata.get("initial_message"),
        phases[0].starting_question if phases else None,
    )

    boundaries = _listify(metadata.get("allowed_topic_boundaries") or metadata.get("allowed_topics"))
    boundaries.extend([scenario.title, scenario.category, *tags, *objectives, objective])
    if variation_prompt:
        boundaries.append(variation_prompt)

    return ScenarioDefinition(
        scenario_id=str(scenario.id),
        title=scenario.title,
        description=scenario.description,
        user_role=user_role,
        ai_role=ai_role,
        objective=objective,
        ai_system_prompt=scenario.ai_system_prompt or "",
        is_ai_start_first=getattr(scenario, "is_ai_start_first", True),
        allowed_topic_boundaries=_dedupe(boundaries),
        phases=phases,
        speaking_style=_first_text(metadata.get("speaking_style"), metadata.get("tone"), "friendly, concise, and natural"),
        difficulty=user_level or scenario.difficulty or "medium",
        expected_intents=_dedupe(_listify(metadata.get("expected_intents")) + objectives + target_skills),
        target_vocabulary=_dedupe(target_vocabulary),
        target_functions=_dedupe(target_functions),
        opening_message=opening,
        metadata={
            "category": scenario.category,
            "mode": scenario.mode,
            "tags": tags,
            "target_skills": target_skills,
            "variation_prompt": variation_prompt,
        },
    )


def _build_phases_from_objectives(objectives: list[str], *, scenario_title: str) -> list[ScenarioPhase]:
    """Build one ScenarioPhase per admin-defined learning objective.

    Each objective text becomes the phase objective verbatim. A contextual
    starting question is derived from the objective wording.

    If no objectives are defined, fall back to a single generic phase so the
    conversation engine never has an empty phases list.
    """
    if not objectives:
        return [
            ScenarioPhase(
                phase_id="conversation",
                title="Open Conversation",
                objective=f"Practice speaking about the {scenario_title} scenario.",
                starting_question=f"What would you like to say in this {scenario_title} situation?",
                expected_intents=[],
                follow_up_questions=[],
            )
        ]

    phases: list[ScenarioPhase] = []
    for index, objective_text in enumerate(objectives):
        phase_id = _slug(objective_text) or f"objective_{index + 1}"
        title = _short_title(objective_text)
        starting_question = _question_for_objective(objective_text, scenario_title)
        phases.append(
            ScenarioPhase(
                phase_id=phase_id,
                title=title,
                objective=objective_text,
                starting_question=starting_question,
                expected_intents=[objective_text],
                follow_up_questions=[],
            )
        )
    return phases


def _short_title(objective: str) -> str:
    """Turn a full objective sentence into a short readable title (≤5 words)."""
    words = re.sub(r"[^a-zA-Z0-9 ]+", "", objective).split()
    return " ".join(words[:5]).title() if words else "Objective"


def _question_for_objective(objective: str, scenario_title: str) -> str:
    """Generate a natural starting question from an objective sentence."""
    lower = objective.lower()
    # Action verbs → interrogative phrasing
    for verb, question_start in [
        ("explain", "Can you explain"),
        ("describe", "Can you describe"),
        ("ask", "Go ahead and ask"),
        ("request", "Please make your request"),
        ("confirm", "Can you confirm"),
        ("clarify", "Can you clarify"),
        ("state", "Please state"),
        ("introduce", "Please introduce"),
        ("greet", "Please greet the other person"),
        ("complain", "Please explain the issue"),
        ("negotiate", "Let's start the negotiation"),
        ("order", "Please go ahead and order"),
        ("book", "Please go ahead and book"),
        ("check", "Please go ahead and check"),
    ]:
        if verb in lower:
            # Remove leading verb from objective to form the object of the question
            question_object = re.sub(rf"^(to )?\b{verb}\b\s*", "", objective, flags=re.IGNORECASE).strip()
            return f"{question_start} {question_object}." if question_object else f"{question_start}."
    return f"How would you handle this part of the {scenario_title} situation?"


def _listify(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, dict):
        return [f"{key}: {item}".strip() for key, item in value.items() if str(item).strip()]
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("[") or text.startswith("{"):
            try:
                return _listify(json.loads(text))
            except json.JSONDecodeError:
                pass
        return [part.strip() for part in re.split(r"[;\n|]+", text) if part.strip()]
    return [str(value).strip()]


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _role_from_prompt(prompt: str | None) -> str:
    if not prompt:
        return ""
    match = re.search(r"you are (?:roleplaying )?(?:as )?(?:a|an)?\s*([^.\n]+)", prompt, flags=re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        clean = value.strip()
        key = clean.lower()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def _slug(value: str) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.lower())).strip("_")[:40]

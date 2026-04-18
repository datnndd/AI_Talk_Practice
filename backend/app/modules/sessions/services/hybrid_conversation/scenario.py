from __future__ import annotations

import json
import re
from typing import Any

from app.modules.scenarios.models.scenario import Scenario
from app.modules.sessions.services.hybrid_conversation.schemas import ScenarioDefinition, ScenarioPhase


DEFAULT_PHASES = [
    ("greeting", "Greeting", "Start the roleplay and establish the learner's need."),
    ("clarify_need", "Clarify Need", "Ask for the key detail needed to move the scenario forward."),
    ("ask_details", "Ask Details", "Collect one useful supporting detail."),
    ("confirm", "Confirm", "Confirm the next step or shared understanding."),
    ("close", "Close", "Close the conversation naturally."),
]


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

    objective = _first_text(
        " ".join(objectives),
        scenario.description,
        "General conversation practice",
    )
    ai_role = _first_text(
        metadata.get("ai_role"),
        metadata.get("persona"),
        metadata.get("partner_persona"),
        _role_from_prompt(scenario.ai_system_prompt),
        "Helpful speaking partner",
    )
    user_role = _first_text(metadata.get("user_role"), metadata.get("learner_role"), "Learner")
    phases = _build_phases(metadata, objective=objective, scenario_title=scenario.title)
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
            "is_ai_start_first": getattr(scenario, "is_ai_start_first", True),
        },
    )


def _build_phases(metadata: dict[str, Any], *, objective: str, scenario_title: str) -> list[ScenarioPhase]:
    raw_phases = metadata.get("suggested_conversation_phases") or metadata.get("phases")
    phases: list[ScenarioPhase] = []
    if isinstance(raw_phases, list) and raw_phases:
        for index, raw in enumerate(raw_phases):
            if isinstance(raw, dict):
                title = _first_text(raw.get("title"), raw.get("name"), f"Phase {index + 1}")
                phase_objective = _first_text(raw.get("objective"), raw.get("goal"), objective)
                question = _first_text(raw.get("starting_question"), raw.get("question"), _question_for_phase(title, scenario_title))
                intents = _listify(raw.get("expected_intents") or raw.get("intents"))
                follow_ups = _listify(raw.get("follow_up_questions") or raw.get("followups"))
            else:
                title = str(raw).strip() or f"Phase {index + 1}"
                phase_objective = _objective_for_phase(title, objective)
                question = _question_for_phase(title, scenario_title)
                intents = []
                follow_ups = []
            phases.append(
                ScenarioPhase(
                    phase_id=_slug(title) or f"phase_{index + 1}",
                    title=title,
                    objective=phase_objective,
                    starting_question=question,
                    expected_intents=intents,
                    follow_up_questions=follow_ups,
                )
            )
    if phases:
        return phases

    return [
        ScenarioPhase(
            phase_id=phase_id,
            title=title,
            objective=_objective_for_phase(title, objective_text=objective),
            starting_question=_question_for_phase(title, scenario_title),
            expected_intents=[],
            follow_up_questions=[],
        )
        for phase_id, title, _ in DEFAULT_PHASES
    ]


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
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", value.lower())).strip("_")


def _objective_for_phase(title: str, objective_text: str) -> str:
    lower = title.lower()
    if "greet" in lower:
        return "Open the conversation and invite the learner to start."
    if "clarify" in lower or "detail" in lower:
        return "Clarify one concrete detail while staying on the scenario objective."
    if "confirm" in lower:
        return "Confirm the learner's meaning and move toward a next step."
    if "close" in lower:
        return "Close the roleplay naturally."
    return objective_text


def _question_for_phase(title: str, scenario_title: str) -> str:
    lower = title.lower()
    if "greet" in lower:
        return "Hi, how can I help you today?"
    if "clarify" in lower:
        return "What do you need help with exactly?"
    if "detail" in lower:
        return "Can you give me one specific detail?"
    if "confirm" in lower:
        return "So what would you like to do next?"
    if "close" in lower:
        return "Is there anything else you want to add before we finish?"
    return f"What would you say in this {scenario_title} situation?"

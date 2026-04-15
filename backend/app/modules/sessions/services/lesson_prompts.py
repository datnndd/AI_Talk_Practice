from __future__ import annotations

import json
import re
from typing import Any

from app.modules.scenarios.models.scenario import Scenario


LESSON_PLAN_SYSTEM_PROMPT = """
You design realistic English speaking practice sessions.

Act as the conversation partner for the selected scenario, not as an English teacher.
Generate a finite conversation plan that adapts to the learner's English level.
Return only valid JSON. Do not include Markdown.
""".strip()


LESSON_PLAN_USER_PROMPT_TEMPLATE = """
Create the initial lesson plan for a live voice conversation.

Scenario:
- Title: {title}
- Description: {description}
- Category: {category}
- Mode: {mode}
- Difficulty: {difficulty}
- Scenario metadata: {metadata}
- Existing learning objectives: {learning_objectives}
- Scenario role prompt: {scenario_prompt}

Learner:
- English level: {level}

Rules:
- The assistant must proactively open the conversation with a natural first question.
- Do not wait for the learner to speak first.
- Stay inside the chosen scenario and role.
- Do not behave like a teacher unless the scenario itself is a teaching scenario.
- Convert vague objectives such as "professional vocabulary" into concrete contextual goals,
  success criteria, and useful phrases.
- Vocabulary must be specific to this exact scenario, not generic labels.
- Follow-up questions must sound like real conversation questions from the role.
- Keep the plan finite:
  - beginner/A1/A2/easy: 2 goals, simple questions, 1-2 follow-ups per goal.
  - intermediate/B1/B2/medium: 3 goals, more detail, 2 follow-ups per goal.
  - advanced/C1/C2/hard: 4 goals, deeper detail, 2-3 follow-ups per goal.

JSON schema:
{{
  "opening_message": "Natural first assistant message. It must include the first question.",
  "goals": [
    {{
      "goal": "Concrete conversation goal",
      "question": "Natural question that starts this goal after the previous goal is complete",
      "success_criteria": ["specific point the learner should include"],
      "follow_up_questions": ["natural follow-up question"],
      "vocabulary": ["contextual word or phrase"]
    }}
  ],
  "summary_instruction": "How to summarize this specific scenario at the end"
}}
""".strip()


def _json_default(value: Any) -> str:
    return str(value)


def _compact_json(value: Any) -> str:
    return json.dumps(value or {}, ensure_ascii=False, default=_json_default)


def _compact_list(value: Any) -> str:
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, default=_json_default)
    if value is None:
        return "[]"
    return json.dumps([str(value)], ensure_ascii=False)


def build_lesson_plan_user_prompt(*, scenario: Scenario, level: str | None) -> str:
    return LESSON_PLAN_USER_PROMPT_TEMPLATE.format(
        title=scenario.title,
        description=scenario.description,
        category=scenario.category,
        mode=scenario.mode,
        difficulty=scenario.difficulty,
        metadata=_compact_json(scenario.scenario_metadata),
        learning_objectives=_compact_list(scenario.learning_objectives),
        scenario_prompt=scenario.ai_system_prompt,
        level=level or "intermediate",
    )


def parse_lesson_plan_response(text: str) -> dict[str, Any] | None:
    stripped = (text or "").strip()
    if not stripped:
        return None

    candidates = [stripped]
    match = re.search(r"\{.*\}", stripped, flags=re.DOTALL)
    if match:
        candidates.append(match.group(0))

    for candidate in candidates:
        try:
            value = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            return value
    return None

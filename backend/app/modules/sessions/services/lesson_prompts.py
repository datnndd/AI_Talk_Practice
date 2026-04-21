from __future__ import annotations

import json
import re
from typing import Any

from app.modules.scenarios.models.scenario import Scenario


LESSON_HINT_SYSTEM_PROMPT = """
You are an English speaking coach helping a Vietnamese learner answer one live roleplay question.
Do not act as the scenario character. Explain what the character is asking and how the learner can answer.
Return ONLY a valid JSON object. Do not add Markdown, code fences, or extra text.
""".strip()


LESSON_HINT_USER_PROMPT_TEMPLATE = """
Create a speaking hint for the learner's current question.

Scenario:
- Title: {title}
- Description: {description}
- Persona asking the question: {persona}
- Learner level: {level}

Current AI question:
{current_question}

Current conversation goal:
{goal}

Expected answer points:
{expected_points}

Useful vocabulary or phrases:
{useful_vocabulary}

Rules:
- Explain the meaning of the current AI question in Vietnamese.
- Give a concise answer strategy in Vietnamese.
- Sample answers must be natural English that the learner can say directly.
- Keep examples short enough for live speaking practice.
- Do not answer as the AI/persona. Answer as the learner/customer/interviewee/user.

Return ONLY this exact JSON structure:

{{
  "question_analysis_vi": "AI dang hoi gi va nguoi hoc can tap trung vao y nao",
  "answer_strategy_vi": "Nen tra loi theo cau truc nao, ngan gon bang tieng Viet",
  "keywords": ["3-6 useful English words or phrases"],
  "sample_answers": [
    "Natural English sample answer 1",
    "Natural English sample answer 2"
  ],
  "simple_answer": "A shorter, easier English answer"
}}
"""


def _json_default(value: Any) -> str:
    return str(value)


def _compact_list(value: Any) -> str:
    if isinstance(value, list):
        return json.dumps(value, ensure_ascii=False, default=_json_default)
    if value is None:
        return "[]"
    return json.dumps([str(value)], ensure_ascii=False)


def build_lesson_hint_user_prompt(
    *,
    scenario: Scenario,
    persona: str,
    level: str | None,
    current_question: str,
    goal: str,
    expected_points: list[str],
    useful_vocabulary: list[str],
) -> str:
    return LESSON_HINT_USER_PROMPT_TEMPLATE.format(
        title=scenario.title,
        description=scenario.description,
        persona=persona,
        level=level or "intermediate",
        current_question=current_question,
        goal=goal,
        expected_points=_compact_list(expected_points),
        useful_vocabulary=_compact_list(useful_vocabulary),
    )


def _parse_json_object_response(text: str) -> dict[str, Any] | None:
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


def parse_lesson_hint_response(text: str) -> dict[str, Any] | None:
    return _parse_json_object_response(text)

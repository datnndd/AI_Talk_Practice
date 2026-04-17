from __future__ import annotations

import json
import re
from typing import Any

from app.modules.scenarios.models.scenario import Scenario


LESSON_PLAN_SYSTEM_PROMPT = """
You are an expert at designing realistic, immersive English speaking practice sessions.
Act strictly as the conversation partner in the given scenario. 
Never act as an English teacher or tutor unless the scenario itself requires it.
Generate a finite, well-structured conversation plan adapted to the learner's CEFR level.
Keep the JSON compact and short enough to fit in one completion.
Return ONLY a valid JSON object. Do not add any explanation, Markdown, or extra text.
""".strip()


LESSON_PLAN_USER_PROMPT_TEMPLATE = """
Create an initial conversation plan for a live voice roleplay.

Scenario:
- Title: {title}
- Description: {description}
- Category: {category}
- Difficulty: {difficulty}
- Scenario role prompt: {scenario_prompt}

Learner English level: {level}

Rules (follow strictly):
- The assistant must open the conversation proactively with a natural, in-character line (diegetic).
- Opening message must sound like the character is speaking inside the scene right now. No meta comments.
- Stay 100% in character and inside the scenario at all times.
- Convert learning objectives into concrete, contextual conversation goals.
- Vocabulary and phrases must be specific to this exact scenario.
- Make every question and follow-up sound like real human conversation from the role.

Level-specific constraints:
- A1/A2 (Beginner/Easy): Maximum 2 goals. Use very simple language. 1 follow-up per goal.
- B1/B2 (Intermediate/Medium): 3 goals. Moderate detail. 1-2 natural follow-ups per goal.
- C1/C2 (Advanced/Hard): 3-4 goals. Deeper, more natural conversation. 2-3 follow-ups per goal.
- Hard output limits:
  - opening_message: max 20 words.
  - goal: max 12 words.
  - starting_question: max 18 words.
  - success_criteria: max 2 items, each max 10 words.
  - follow_up_questions: max 2 items, each max 14 words.
  - useful_phrases: max 3 items, each max 8 words.
  - ending_summary_instruction: max 18 words.
- Use compact JSON strings. Do not include long explanations.

Return ONLY this exact JSON structure (no extra fields, no extra text):

{{
  "opening_message": "Natural first line said by the character (max 15-20 words)",
  "goals": [
    {{
      "goal": "Short, concrete conversation goal",
      "starting_question": "Natural question the character asks to begin this goal",
      "success_criteria": ["What the learner should try to communicate (specific points)"],
      "follow_up_questions": ["Natural follow-up 1", "Natural follow-up 2"],
      "useful_phrases": ["1-3 contextual phrases or vocabulary useful for this goal"]
    }}
  ],
  "ending_summary_instruction": "Brief instruction for how to end the conversation naturally and give light feedback"
}}
"""


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


def parse_lesson_plan_response(text: str) -> dict[str, Any] | None:
    return _parse_json_object_response(text)


def parse_lesson_hint_response(text: str) -> dict[str, Any] | None:
    return _parse_json_object_response(text)

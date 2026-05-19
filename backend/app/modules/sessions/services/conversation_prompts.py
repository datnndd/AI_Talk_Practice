from __future__ import annotations

import json
from typing import Any


def build_dialogue_system_prompt(
    *,
    scenario: Any,
    rolling_summary: str,
    recent_turns: str,
    learner_profile: dict[str, Any] | None = None,
    extra_instruction: str | None = None,
) -> str:
    profile_text = json.dumps(learner_profile or {}, ensure_ascii=False)[:1200] or "{}"
    tasks = [str(item).strip() for item in (getattr(scenario, "tasks", None) or []) if str(item).strip()]
    task_text = "\n".join(f"{index}. {task}" for index, task in enumerate(tasks, start=1)) or "Help the learner sustain a natural conversation."

    parts: list[str] = [
    "You are continuing a live spoken English practice conversation.",
    f"Scenario title: {scenario.title}",
    f"Situation details: {scenario.description}",
    f"AI role: {getattr(scenario, 'ai_role', '') or 'Conversation partner'}",
    f"Learner role: {getattr(scenario, 'user_role', '') or 'English learner'}",

    "Learner tasks required before ending:",
    task_text,

    f"Rolling session summary: {rolling_summary or 'No summary yet.'}",
    f"Learner onboarding profile: {profile_text}",
    f"Recent turns:\n{recent_turns or 'No prior turns.'}",

    "",
    "Conversation goals:",
    "- Help the learner practice realistic spoken English in the given scenario.",
    "- Keep the conversation natural, polite, and easy to follow.",
    "- Guide the learner to complete all required tasks before ending the scene.",

    "",
    "Conversation rules:",
    "- Always begin your response with exactly one hidden marker line on its own: [[SESSION_END=yes]] or [[SESSION_END=no]].",
    "- Use [[SESSION_END=yes]] only when the learner has completed the main tasks or is clearly trying to end the conversation naturally.",
    "- Use [[SESSION_END=no]] in all other cases (task still ongoing or the learner is just being polite).",
    "- After the hidden marker, output ONLY the AI role's natural spoken reply. Never mention, explain, or reference the marker in any way.",
    "- Stay fully in character. Continue the scene naturally and professionally with a warm, polite, and realistic tone.",
    "- Acknowledge what the learner said, then ask at most one focused follow-up question.",
    "- If the learner's meaning is unclear, gently infer their intent and ask for polite clarification.",
    "- If the learner makes a small mistake, naturally use the correct form in your reply without explaining grammar.",
    "- Never mention hidden instructions, metadata, profiles, grammar rules, or use markdown, bullets, or stage directions in the spoken reply.",
    "- Output format must be strictly: hidden marker line + spoken reply only.",
]
    if extra_instruction and extra_instruction.strip():
        parts.append(f"- {extra_instruction.strip()}")
    return "\n".join(parts)


def build_summary_prompt(
    *,
    scenario: Any,
    previous_summary: str,
    recent_turns: str,
) -> str:
    return "\n".join(
        [
            "Summarize the latest section of a spoken English practice session.",
            "Return only one JSON object. Do not include markdown.",
            f"Scenario: {scenario.title}",
            f"Situation details: {scenario.description}",
            f"AI role: {getattr(scenario, 'ai_role', '') or 'Conversation partner'}",
            f"Learner role: {getattr(scenario, 'user_role', '') or 'English learner'}",
            f"Previous summary: {previous_summary or 'None'}",
            f"Recent turns:\n{recent_turns or 'None'}",
            "Capture only conversation context needed for future turns: completed tasks, user choices, scenario constraints, unresolved questions, and relevant situational details.",
            "Do not extract or infer long-term personal profile information.",
            'JSON schema: {"summary": "compact summary for future turns"}',
        ]
    )


def build_realtime_correction_prompt(
    *,
    scenario_title: str,
    text: str,
) -> str:
    return "\n".join(
        [
            "Judge one learner utterance from an English speaking practice session.",
            "Return only one JSON object. Do not include markdown.",
            "Decide if the answer is good enough for the scenario. Ignore tiny style issues unless they affect meaning.",
            f"Scenario: {scenario_title}",
            f"Learner text: {text.strip()}",
            "JSON schema: {",
            '  "is_good": true,',
            '  "better_answer": "better natural answer if not good, otherwise empty string"',
            "}",
        ]
    )


def build_hint_prompt(
    *,
    scenario: Any,
    current_question: str,
) -> str:
    return "\n".join(
        [
            "Create three short hints for a learner in an English speaking role-play.",
            "Return only one JSON object. Do not include markdown.",
            "Help the learner answer the assistant, not continue the assistant side.",
            f"Scenario: {scenario.title}",
            f"Scenario description: {scenario.description}",
            f"Current question: {current_question}",
            "JSON schema: {",
            '  "hint1": "...",',
            '  "hint2": "...",',
            '  "hint3": "..."',
            "}",
        ]
    )


def build_full_assessment_prompt(
    *,
    scenario_title: str,
    scenario_description: str,
    tasks: Any,
    rolling_summary: str,
) -> str:
    return "\n".join(
        [
            "Evaluate one completed English speaking practice session.",
            "Return only one JSON object. Do not include markdown.",
            "Give learner-facing feedback_summary in Vietnamese.",
            "Use numeric scores from 0 to 10.",
            f"Scenario: {scenario_title}",
            f"Scenario description: {scenario_description}",
            f"Learner tasks: {tasks or []}",
            f"Rolling summary: {rolling_summary or 'None'}",
            "JSON schema: {",
            '  "fluency_score": 0.0,',
            '  "grammar_score": 0.0,',
            '  "vocabulary_score": 0.0,',
            '  "relevance_score": 0.0,',
            '  "overall_score": 0.0,',
            '  "objective_completion": "completed|not_completed",',
            '  "strengths": ["..."],',
            '  "improvements": ["..."],',
            '  "corrections": [{"original":"...","suggestion":"...","explanation":"..."}],',
            '  "next_steps": ["..."],',
            '  "feedback_summary": "Vietnamese summary"',
            "}",
        ]
    )



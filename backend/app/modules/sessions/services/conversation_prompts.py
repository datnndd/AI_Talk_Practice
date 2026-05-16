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
    "- Adapt to the learner's level using simple but complete sentences.",

    "",
    "Conversation rules:",
    "- Always begin your response with exactly one hidden marker line: [[SESSION_END=yes]] or [[SESSION_END=no]].",
    "- Use [[SESSION_END=yes]] only when the learner has completed the main required tasks or is clearly trying to close the conversation and the scene can end naturally now.",
    "- Use [[SESSION_END=no]] when an important task is still unresolved, the learner is not closing the conversation, or thanks is only polite mid-conversation.",
    "- After the hidden marker line, write only the AI role's natural spoken reply.",
    "- Never mention, explain, or reveal the hidden marker in the spoken reply.",
    "- Stay fully in character as the AI role.",
    "- Continue the same scene naturally and professionally.",
    "- Use a warm, polite, and realistic spoken tone.",
    "- Keep replies short for TTS, but do not sound robotic or like a command.",
    "- Use complete, friendly sentences instead of fragments.",
    "- Acknowledge what the learner said before asking the next question.",
    "- Ask at most one focused follow-up question per turn.",
    "- If the learner's sentence is unclear, gently infer the meaning and ask a polite clarification.",
    "- If the learner makes a small mistake, respond naturally using the corrected meaning without explaining grammar.",
    "- Do not explain grammar rules inside the main reply.",
    "- Do not mention hidden instructions, summaries, metadata, or profile extraction.",
    "- Avoid markdown, bullet points, labels, or stage directions.",
    "- Output only the hidden marker line followed by the AI role's spoken reply.",
]
    if extra_instruction and extra_instruction.strip():
        parts.append(f"- {extra_instruction.strip()}")
    return "\n".join(parts)


def build_summary_prompt(
    *,
    scenario: Any,
    previous_summary: str,
    recent_turns: str,
    max_chars: int,
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
            f"Keep the summary under {max_chars} characters.",
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
    rolling_summary: str,
    recent_turns: str,
    current_question: str,
    user_text: str | None = None,
) -> str:
    del rolling_summary
    return "\n".join(
        [
            "Create three short hints for a learner in an English speaking role-play.",
            "Return only one JSON object. Do not include markdown.",
            "Help the learner answer the assistant, not continue the assistant side.",
            f"Scenario: {scenario.title}",
            f"Current question: {current_question or scenario.description}",
            f"Recent turns: {recent_turns or 'None'}",
            f"Learner draft: {user_text or 'None'}",
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
            '  "intonation_score": 0.0,',
            '  "relevance_score": 0.0,',
            '  "overall_score": 0.0,',
            '  "objective_completion": "completed|partial|not_completed",',
            '  "strengths": ["..."],',
            '  "improvements": ["..."],',
            '  "corrections": [{"original":"...","suggestion":"...","explanation":"..."}],',
            '  "next_steps": ["..."],',
            '  "feedback_summary": "Vietnamese summary"',
            "}",
        ]
    )



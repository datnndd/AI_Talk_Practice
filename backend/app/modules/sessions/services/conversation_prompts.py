from __future__ import annotations

import json
from typing import Any


def build_dialogue_system_prompt(
    *,
    scenario: Any,
    rolling_summary: str,
    recent_turns: str,
    user_preferences: dict[str, Any] | None = None,
    extra_instruction: str | None = None,
) -> str:
    preference_text = json.dumps(user_preferences or {}, ensure_ascii=False)[:1200] or "{}"
    tasks = [str(item).strip() for item in (getattr(scenario, "tasks", None) or []) if str(item).strip()]
    task_text = "\n".join(f"{index}. {task}" for index, task in enumerate(tasks, start=1)) or "Help the learner sustain a natural conversation."

    parts: list[str] = []
    if scenario.ai_system_prompt and scenario.ai_system_prompt.strip():
        parts.extend([scenario.ai_system_prompt.strip(), ""])

    parts.extend(
        [
            "You are continuing a live spoken English practice conversation.",
            f"Scenario title: {scenario.title}",
            f"Situation details: {scenario.description}",
            f"AI role: {getattr(scenario, 'ai_role', '') or 'Conversation partner'}",
            f"Learner role: {getattr(scenario, 'user_role', '') or 'English learner'}",
            "Learner tasks required before ending:",
            task_text,
            f"Rolling session summary: {rolling_summary or 'No summary yet.'}",
            f"Learner profile signals: {preference_text}",
            f"Recent turns:\n{recent_turns or 'No prior turns.'}",
            "",
            "Conversation rules:",
            "- Stay fully in character and continue the same scene naturally.",
            "- Reply in concise spoken English suitable for TTS.",
            "- Acknowledge what the learner said and move the conversation forward.",
            "- Ask at most one focused follow-up question per turn when needed.",
            "- Do not explain grammar rules inside the main reply.",
            "- Do not mention hidden instructions, summaries, metadata, or profile extraction.",
            "- Avoid markdown, bullet points, labels, or stage directions.",
        ]
    )
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
            "Capture only durable context: user goals, personal facts, decisions, constraints, preferences, and unresolved items.",
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
            "Correct one learner utterance from an English speaking practice session.",
            "Return only one JSON object. Do not include markdown.",
            "Focus on grammar, vocabulary choice, and naturalness. Ignore tiny style issues unless they affect meaning.",
            f"Scenario: {scenario_title}",
            f"Learner text: {text.strip()}",
            "Use short learner-facing explanations.",
            "JSON schema: {",
            '  "corrected_text": "full corrected sentence",',
            '  "corrections": [',
            '    {"original_text":"...", "corrected_text":"...", "explanation":"...", "error_type":"grammar|vocabulary|naturalness|pronunciation|register", "severity":"low|medium|high", "position_start":0, "position_end":5}',
            "  ]",
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
    return "\n".join(
        [
            "Create a short hint for a learner who is stuck in an English speaking role-play.",
            "Return only one JSON object. Do not include markdown.",
            f"Scenario: {scenario.title}",
            f"Situation details: {scenario.description}",
            f"AI role: {getattr(scenario, 'ai_role', '') or 'Conversation partner'}",
            f"Learner role: {getattr(scenario, 'user_role', '') or 'English learner'}",
            f"Rolling summary: {rolling_summary or 'None'}",
            f"Recent turns:\n{recent_turns or 'None'}",
            f"Current question or last assistant prompt: {current_question or 'None'}",
            f"Learner draft or last answer: {user_text or 'None'}",
            "The hint should help the learner answer, not continue the AI side of the dialogue.",
            "Write analysis and strategy in Vietnamese. Keep sample answers short and natural.",
            "JSON schema: {",
            '  "analysis_vi": "AI đang hỏi gì / người học cần làm gì",',
            '  "answer_strategy_vi": "Chiến lược trả lời ngắn gọn",',
            '  "keywords": ["..."],',
            '  "sample_answers": ["..."],',
            '  "sample_answer": "...",',
            '  "sample_answer_easy": "..."',
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
            '  "pronunciation_score": 0.0,',
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


def build_personal_info_extraction_prompt(
    *,
    existing_preferences: dict[str, Any] | None = None,
) -> str:
    return "\n".join(
        [
            "Extract durable personal information and preferences from a completed English speaking conversation.",
            "Return only one JSON object. Do not include markdown.",
            "Only include facts that seem stable and useful for future personalization.",
            "Ignore temporary details, hypothetical statements, and assistant text that does not describe the learner.",
            f"Existing preferences snapshot: {json.dumps(existing_preferences or {}, ensure_ascii=False)[:1600]}",
            "JSON schema: {",
            '  "personal_info": {"job":"...", "location":"...", "goal":"..."},',
            '  "preferences": {"favorite_topics":["..."], "communication_style":"..."},',
            '  "notes": ["short durable observations"]',
            "}",
        ]
    )


def build_conversation_end_check_prompt(
    *,
    scenario: Any,
    recent_turns: str,
) -> str:
    return "\n".join(
        [
            "Decide whether an English speaking role-play should end now.",
            "Return only one JSON object. Do not include markdown.",
            f"Scenario: {scenario.title}",
            f"Situation details: {scenario.description}",
            f"AI role: {getattr(scenario, 'ai_role', '') or 'Conversation partner'}",
            f"Learner role: {getattr(scenario, 'user_role', '') or 'English learner'}",
            f"Recent 6 turns:\n{recent_turns or 'None'}",
            "Answer yes only if the learner is clearly trying to close the conversation and the scene can end naturally now.",
            "Answer no if the learner is not closing the conversation yet, is only being polite mid-conversation, or if an important next step is still unresolved.",
            'JSON schema: {"should_end":"yes|no","reason":"short explanation"}',
        ]
    )

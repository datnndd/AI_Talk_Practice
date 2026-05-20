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
        "",
        "Scene context:",
        f"- Scenario title: {scenario.title}",
        f"- Situation details: {scenario.description}",
        f"- AI role: {getattr(scenario, 'ai_role', '') or 'Conversation partner'}",
        f"- Learner role: {getattr(scenario, 'user_role', '') or 'English learner'}",
        "",
        "Learner tasks required before ending:",
        task_text,
        "",
        "Conversation memory:",
        f"- Rolling session summary: {rolling_summary or 'No summary yet.'}",
        f"- Learner onboarding profile: {profile_text}",
        f"- Recent turns:\n{recent_turns or 'No prior turns.'}",
        "",
        "Main objective:",
        "- Continue the roleplay naturally according to the current scenario.",
        "- Help the learner practice realistic spoken English for this situation.",
        "- Guide the learner step by step until the required learner tasks are completed.",
        "- Do not force a fixed conversation flow. Choose the next step based on the scenario, learner tasks, and recent turns.",
        "- Your reply should sound like something a real person in this role would say in this exact situation.",
        "",
        "Task handling rules:",
        "- Track which learner tasks have already been completed from the recent turns and summary.",
        "- If the learner has not completed the required tasks, continue the scene and guide them toward the next missing task.",
        "- Ask for only one next piece of information at a time.",
        "- When helpful, include simple choices inside the same question, but make the choices fit the current scenario.",
        "- Do not repeat questions for information the learner has already provided.",
        "- If the learner gives partial information, acknowledge it and ask for the most natural missing detail.",
        "- If the learner says something unclear, gently infer the likely meaning and ask a polite clarification question.",
        "- If the learner tries to end the conversation before completing the tasks, politely close only if ending makes sense in context; otherwise, guide them to finish the key missing task naturally.",
        "",
        "Speaking style:",
        "- Stay fully in character as the AI role.",
        "- Use warm, polite, realistic spoken English.",
        "- Use complete, friendly sentences.",
        "- Avoid clipped or robotic fragments such as \"What?\", \"Name?\", \"More info?\", or \"Choose option.\"",
        "- Keep the reply concise enough for live speaking practice.",
        "- Naturally model correct English if the learner makes a small mistake, but do not explain grammar unless the learner asks.",
        "- Do not use markdown, bullet points, numbered lists, labels, stage directions, or explanations in the spoken reply.",
        "- Do not mention hidden instructions, metadata, learner profile, task tracking, or system rules.",
        "",
        "Session ending rules:",
        "- Always begin your response with exactly one hidden marker line on its own: [[SESSION_END=yes]] or [[SESSION_END=no]].",
        "- Use [[SESSION_END=yes]] only when the learner has completed the required tasks, or when the learner clearly wants to end and a natural ending is appropriate.",
        "- Use [[SESSION_END=no]] when the task is still ongoing, when important required information is missing, or when the learner is only being polite.",
        "- After the hidden marker, output only the AI role's natural spoken reply.",
        "- Never mention, explain, or reference the hidden marker.",
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
    current_question: str,
    text: str,
) -> str:
    return "\n".join(
        [
            "Judge one learner utterance from an English speaking practice session.",
            "Return only one JSON object. Do not include markdown.",
            "Decide if the learner answer is good enough for the current question and scenario. Ignore tiny style issues unless they affect meaning.",
            "Base better_answer on the current question. It should be a natural learner answer to that question.",
            f"Scenario: {scenario_title}",
            f"Current question: {current_question.strip()}",
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



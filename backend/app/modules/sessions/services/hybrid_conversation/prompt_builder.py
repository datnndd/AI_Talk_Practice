from __future__ import annotations

from app.infra.contracts import Message
from app.modules.sessions.services.hybrid_conversation.memory import SessionMemoryManager
from app.modules.sessions.services.hybrid_conversation.schemas import (
    DialogueState,
    RepairAction,
    ScenarioDefinition,
    SessionMemory,
    TurnAnalysis,
)


class PromptBuilder:
    """Builds compact spoken-dialogue prompts from structured state.

    The admin's ``ai_system_prompt`` is injected as the first block so the
    AI's persona and behaviour rules are always respected.  Structured
    context (phase, memory, policy) is appended after so the engine can
    steer the conversation without overriding character.
    """

    def build(
        self,
        *,
        scenario: ScenarioDefinition,
        memory: SessionMemory,
        state: DialogueState,
        user_text: str,
        repair_action: RepairAction,
        turn_analysis: TurnAnalysis | None = None,
    ) -> tuple[str, list[Message]]:
        phase = scenario.current_or_first_phase(state.current_phase_id)
        compact = SessionMemoryManager(
            memory,
            max_facts=max(1, len(memory.facts) or 1),
            recent_turn_limit=max(1, len(memory.recent_turns) or 1),
            summary_max_chars=800,
        ).compact_export()

        facts_line = compact["facts"] or "None"
        summary_line = compact["summary"] or "No prior summary."
        boundaries = "; ".join(scenario.allowed_topic_boundaries[:8]) or scenario.title
        vocabulary = ", ".join(scenario.target_vocabulary[:8]) or "No required vocabulary."
        analysis_line = (
            f"{turn_analysis.label.value}, relevance={turn_analysis.relevance_score:.2f}, "
            f"intent={turn_analysis.intent or 'unknown'}, reason={turn_analysis.reason}"
            if turn_analysis
            else "No analysis available."
        )

        parts: list[str] = []

        # --- Admin-authored persona block (injected first, verbatim) ---
        if scenario.ai_system_prompt and scenario.ai_system_prompt.strip():
            parts.append(scenario.ai_system_prompt.strip())
            parts.append("")  # blank separator

        # --- Structural context block ---
        parts.extend(
            [
                f"Scenario: {scenario.title}",
                f"Situation Context: {scenario.description}",
                f"AI role: {scenario.ai_role}",
                f"Learner role: {scenario.user_role}",
                f"Overall mission: {scenario.objective}",
                f"Current phase: {phase.title} — {phase.objective}",
                f"Current phase question to resolve: {phase.starting_question}",
                "",
                f"Relevant learner facts: {facts_line}",
                f"Recent compact summary: {summary_line}",
                f"Target vocabulary/functions: {vocabulary}",
                f"Dialogue policy: {repair_action.action.value} ({repair_action.reason})",
                f"Turn analysis: {analysis_line}",
                "",
                # Behavioural guard-rails
                "Rules:",
                "- Stay centered on the situation context and current phase mission.",
                "- If the learner drifts off-topic, acknowledge briefly and steer back.",
                "- Keep replies concise, conversational, and optimised for speech.",
                "- Ask one focused question at a time.",
                "- Do not use markdown, bullets, or long paragraphs.",
                "- Reuse learner facts only when it feels natural.",
                f"- Speaking style: {scenario.speaking_style}.",
            ]
        )

        system_prompt = "\n".join(parts)
        return system_prompt, [Message(role="user", content=user_text.strip())]

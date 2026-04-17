from __future__ import annotations

from app.infra.contracts import Message
from app.services.conversation.memory import SessionMemoryManager
from app.services.conversation.schemas import DialogueState, RepairAction, ScenarioDefinition, SessionMemory


class PromptBuilder:
    """Builds compact spoken-dialogue prompts from structured state."""

    def build(
        self,
        *,
        scenario: ScenarioDefinition,
        memory: SessionMemory,
        state: DialogueState,
        user_text: str,
        repair_action: RepairAction,
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

        system_prompt = "\n".join(
            [
                "You are running a real-time spoken English practice conversation.",
                f"Scenario: {scenario.title}",
                f"AI role: {scenario.ai_role}",
                f"Learner role: {scenario.user_role}",
                f"Objective: {scenario.objective}",
                f"Current phase: {phase.title} - {phase.objective}",
                f"Topic boundaries: {boundaries}",
                f"Relevant learner facts: {facts_line}",
                f"Recent compact summary: {summary_line}",
                f"Target vocabulary/functions: {vocabulary}",
                f"Dialogue policy: {repair_action.action.value} ({repair_action.reason})",
                "Stay centered on the scenario objective.",
                "Reuse learner facts only when it feels natural and useful.",
                "If the learner drifts, acknowledge briefly and steer back.",
                "Keep the reply concise, conversational, and optimized for speech.",
                "Ask one focused question at a time.",
                "Do not use markdown, bullets, or long paragraphs.",
            ]
        )
        return system_prompt, [Message(role="user", content=user_text.strip())]

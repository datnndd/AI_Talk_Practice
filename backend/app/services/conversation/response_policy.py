from __future__ import annotations

from app.services.conversation.schemas import (
    DialogueState,
    PolicyAction,
    RepairAction,
    ScenarioDefinition,
    TurnAnalysis,
    TurnLabel,
)


class ResponsePolicy:
    """Chooses deterministic repair behavior or allows LLM generation."""

    def __init__(self, *, repair_max_repeats: int = 2):
        self.repair_max_repeats = max(1, int(repair_max_repeats))

    def decide(
        self,
        analysis: TurnAnalysis,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
    ) -> RepairAction:
        if analysis.label == TurnLabel.NONSENSE:
            return RepairAction(action=PolicyAction.REASK, reason="nonsense_or_low_confidence")
        if analysis.label == TurnLabel.TOO_SHORT:
            return RepairAction(action=PolicyAction.NARROW_QUESTION, reason="answer_too_short")
        if analysis.label == TurnLabel.HELP_REQUEST:
            return RepairAction(action=PolicyAction.HINT, reason="user_requested_help")
        if analysis.label == TurnLabel.CLARIFICATION_REQUEST:
            return RepairAction(action=PolicyAction.HINT, reason="user_requested_clarification")
        if analysis.label == TurnLabel.OFF_TOPIC:
            if analysis.contains_useful_personal_fact:
                return RepairAction(action=PolicyAction.ACKNOWLEDGE_AND_STEER, reason="off_topic_with_useful_fact")
            return RepairAction(action=PolicyAction.REDIRECT, reason="off_topic")
        if analysis.label == TurnLabel.PARTIALLY_ON_TOPIC and not analysis.contains_direct_answer:
            return RepairAction(action=PolicyAction.ACKNOWLEDGE_AND_STEER, reason="partial_without_progress")
        return RepairAction(action=PolicyAction.GENERATE, reason="on_topic_progress")

    def repair_text(
        self,
        action: RepairAction,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        analysis: TurnAnalysis,
    ) -> str:
        phase = scenario.current_or_first_phase(state.current_phase_id)
        question = phase.starting_question
        if action.action == PolicyAction.REASK:
            return f"I didn't catch a clear answer. Please try again: {question}"
        if action.action == PolicyAction.NARROW_QUESTION:
            return f"Good start. Add one concrete detail. {question}"
        if action.action == PolicyAction.HINT:
            sample = self._sample_hint(scenario, phase_title=phase.title)
            return f"You can say: \"{sample}\" Now try your own answer: {question}"
        if action.action == PolicyAction.ACKNOWLEDGE_AND_STEER:
            return f"Thanks, I'll remember that. For this practice, {question}"
        if action.action == PolicyAction.REDIRECT:
            return f"Let's stay with the roleplay. {question}"
        return ""

    def _sample_hint(self, scenario: ScenarioDefinition, *, phase_title: str) -> str:
        if scenario.target_functions:
            return f"I need help with this, and I can share more details."
        if "interview" in scenario.title.lower():
            return "I have experience with this, and I can give an example."
        if "order" in scenario.title.lower():
            return "I'd like to order this, please."
        return "I need help with this task."

from __future__ import annotations

from app.modules.sessions.services.hybrid_conversation.schemas import DialogueState, ScenarioDefinition, TurnAnalysis, TurnLabel


REPAIR_LABELS = {
    TurnLabel.NONSENSE,
    TurnLabel.TOO_SHORT,
    TurnLabel.HELP_REQUEST,
    TurnLabel.CLARIFICATION_REQUEST,
    TurnLabel.OFF_TOPIC,
}


class DialogueStateController:
    """Soft state controller that advances phases on useful progress."""

    def apply_turn(
        self,
        state: DialogueState,
        *,
        scenario: ScenarioDefinition,
        analysis: TurnAnalysis,
    ) -> DialogueState:
        next_state = state.model_copy(deep=True)
        next_state.turn_index += 1
        next_state.last_analysis_label = analysis.label

        if analysis.label in REPAIR_LABELS:
            next_state.repair_count += 1
        else:
            next_state.repair_count = 0

        if analysis.label == TurnLabel.ON_TOPIC and analysis.contains_direct_answer:
            self._advance_phase_if_possible(next_state, scenario)

        return next_state

    def _advance_phase_if_possible(self, state: DialogueState, scenario: ScenarioDefinition) -> None:
        phase_ids = [phase.phase_id for phase in scenario.phases]
        if not phase_ids or state.current_phase_id not in phase_ids:
            return

        current_index = phase_ids.index(state.current_phase_id)
        if state.current_phase_id not in state.completed_phase_ids:
            state.completed_phase_ids.append(state.current_phase_id)

        if current_index + 1 < len(phase_ids):
            state.current_phase_id = phase_ids[current_index + 1]
            state.phase_history.append(state.current_phase_id)
            return

        state.should_end = True
        state.end_reason = "scenario_objective_completed"

from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class TurnLabel(str, Enum):
    ON_TOPIC = "on_topic"
    PARTIALLY_ON_TOPIC = "partially_on_topic"
    OFF_TOPIC = "off_topic"
    NONSENSE = "nonsense"
    HELP_REQUEST = "help_request"
    TOO_SHORT = "too_short"
    CLARIFICATION_REQUEST = "clarification_request"


class PolicyAction(str, Enum):
    GENERATE = "generate"
    REASK = "reask"
    NARROW_QUESTION = "narrow_question"
    HINT = "hint"
    REDIRECT = "redirect"
    ACKNOWLEDGE_AND_STEER = "acknowledge_and_steer"


class ScenarioPhase(BaseModel):
    phase_id: str
    title: str
    objective: str
    starting_question: str
    expected_intents: list[str] = Field(default_factory=list)
    follow_up_questions: list[str] = Field(default_factory=list)


class ScenarioDefinition(BaseModel):
    scenario_id: str
    title: str
    description: str
    user_role: str
    ai_role: str
    objective: str
    allowed_topic_boundaries: list[str] = Field(default_factory=list)
    phases: list[ScenarioPhase] = Field(default_factory=list)
    speaking_style: str = "friendly, concise, and natural"
    difficulty: str = "medium"
    expected_intents: list[str] = Field(default_factory=list)
    target_vocabulary: list[str] = Field(default_factory=list)
    target_functions: list[str] = Field(default_factory=list)
    opening_message: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def current_or_first_phase(self, phase_id: str | None = None) -> ScenarioPhase:
        if phase_id:
            for phase in self.phases:
                if phase.phase_id == phase_id:
                    return phase
        if self.phases:
            return self.phases[0]
        return ScenarioPhase(
            phase_id="conversation",
            title="Conversation",
            objective=self.objective,
            starting_question=self.opening_message or "What would you like to say first?",
            expected_intents=self.expected_intents,
        )


class MemoryFact(BaseModel):
    key: str
    value: str
    category: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    source_turn_index: int = 0
    relevance_to_scenario: float = Field(default=0.5, ge=0.0, le=1.0)
    last_used_turn: int | None = None


class DialogueTurn(BaseModel):
    turn_index: int
    user_text: str
    assistant_text: str | None = None
    analysis_label: TurnLabel | None = None


class SessionMemory(BaseModel):
    scenario_id: str
    current_objective: str
    current_phase_id: str
    facts: list[MemoryFact] = Field(default_factory=list)
    recent_turns: list[DialogueTurn] = Field(default_factory=list)
    recent_dialogue_summary: str = ""
    user_preferences: dict[str, str] = Field(default_factory=dict)
    emotional_context: dict[str, str] = Field(default_factory=dict)
    unresolved_questions: list[str] = Field(default_factory=list)
    last_repair_reason: str | None = None


class TurnAnalysis(BaseModel):
    text: str
    label: TurnLabel
    labels: list[TurnLabel] = Field(default_factory=list)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    intent: str | None = None
    contains_useful_personal_fact: bool = False
    contains_direct_answer: bool = False
    contains_clarification_request: bool = False
    extracted_fact_keys: list[str] = Field(default_factory=list)
    reason: str = ""


class DialogueState(BaseModel):
    scenario_id: str
    current_phase_id: str
    turn_index: int = 0
    repair_count: int = 0
    completed_phase_ids: list[str] = Field(default_factory=list)
    phase_history: list[str] = Field(default_factory=list)
    last_analysis_label: TurnLabel | None = None
    should_end: bool = False
    end_reason: str | None = None


class RepairAction(BaseModel):
    action: PolicyAction
    reason: str
    message: str | None = None


class OrchestratorInput(BaseModel):
    user_text: str
    session_id: int | None = None


class OrchestratorOutput(BaseModel):
    assistant_text: str
    analysis: TurnAnalysis
    repair_action: RepairAction
    dialogue_state: DialogueState
    memory: SessionMemory

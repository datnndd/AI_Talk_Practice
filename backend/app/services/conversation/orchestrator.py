from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

from app.core.config import settings
from app.infra.contracts import LLMBase
from app.modules.sessions.schemas.lesson import LessonObjectiveState, LessonProgressSummary, LessonStateRead
from app.services.conversation.analyzer import TopicAnalyzer
from app.services.conversation.evaluation import NoOpEvaluationHook, PostTurnEvaluationHook
from app.services.conversation.fact_extractor import RuleBasedFactExtractor
from app.services.conversation.memory import SessionMemoryManager
from app.services.conversation.prompt_builder import PromptBuilder
from app.services.conversation.response_policy import ResponsePolicy
from app.services.conversation.schemas import (
    DialogueState,
    OrchestratorOutput,
    PolicyAction,
    RepairAction,
    ScenarioDefinition,
    SessionMemory,
    TurnAnalysis,
)
from app.services.conversation.state_controller import DialogueStateController

logger = logging.getLogger(__name__)


class DialogueOrchestrator:
    """Coordinates memory, topic control, state progression, prompting, and LLM replies."""

    def __init__(
        self,
        *,
        scenario: ScenarioDefinition,
        llm: LLMBase,
        memory: SessionMemory,
        state: DialogueState,
        max_facts: int,
        recent_turn_limit: int,
        summary_max_chars: int,
        repair_max_repeats: int,
        evaluator: PostTurnEvaluationHook | None = None,
    ):
        self.scenario = scenario
        self.llm = llm
        self.memory = SessionMemoryManager(
            memory,
            max_facts=max_facts,
            recent_turn_limit=recent_turn_limit,
            summary_max_chars=summary_max_chars,
        )
        self.state = state
        self.fact_extractor = RuleBasedFactExtractor()
        self.analyzer = TopicAnalyzer(
            on_topic_threshold=settings.conversation_relevance_on_topic_threshold,
            partial_threshold=settings.conversation_relevance_partial_threshold,
        )
        self.state_controller = DialogueStateController()
        self.policy = ResponsePolicy(repair_max_repeats=repair_max_repeats)
        self.prompt_builder = PromptBuilder()
        self.evaluator = evaluator or NoOpEvaluationHook()
        self.last_output: OrchestratorOutput | None = None

    @classmethod
    def create(
        cls,
        *,
        scenario: ScenarioDefinition,
        llm: LLMBase,
        max_facts: int,
        recent_turn_limit: int,
        summary_max_chars: int,
        repair_max_repeats: int,
    ) -> "DialogueOrchestrator":
        first_phase = scenario.current_or_first_phase()
        memory = SessionMemory(
            scenario_id=scenario.scenario_id,
            current_objective=scenario.objective,
            current_phase_id=first_phase.phase_id,
        )
        state = DialogueState(
            scenario_id=scenario.scenario_id,
            current_phase_id=first_phase.phase_id,
            phase_history=[first_phase.phase_id],
        )
        return cls(
            scenario=scenario,
            llm=llm,
            memory=memory,
            state=state,
            max_facts=max_facts,
            recent_turn_limit=recent_turn_limit,
            summary_max_chars=summary_max_chars,
            repair_max_repeats=repair_max_repeats,
        )

    @classmethod
    def from_metadata(
        cls,
        *,
        scenario: ScenarioDefinition,
        llm: LLMBase,
        metadata: dict[str, Any] | None,
        max_facts: int,
        recent_turn_limit: int,
        summary_max_chars: int,
        repair_max_repeats: int,
    ) -> "DialogueOrchestrator":
        data = dict((metadata or {}).get("hybrid_conversation") or {})
        if not data:
            return cls.create(
                scenario=scenario,
                llm=llm,
                max_facts=max_facts,
                recent_turn_limit=recent_turn_limit,
                summary_max_chars=summary_max_chars,
                repair_max_repeats=repair_max_repeats,
            )

        memory = SessionMemory.model_validate(data.get("memory") or {})
        state = DialogueState.model_validate(data.get("dialogue_state") or {})
        return cls(
            scenario=scenario,
            llm=llm,
            memory=memory,
            state=state,
            max_facts=max_facts,
            recent_turn_limit=recent_turn_limit,
            summary_max_chars=summary_max_chars,
            repair_max_repeats=repair_max_repeats,
        )

    def to_metadata(self) -> dict[str, Any]:
        return {
            "memory": self.memory.memory.model_dump(mode="json"),
            "dialogue_state": self.state.model_dump(mode="json"),
            "scenario_definition": self.scenario.model_dump(mode="json"),
        }

    def opening_message(self) -> str:
        phase = self.scenario.current_or_first_phase(self.state.current_phase_id)
        return self.scenario.opening_message or phase.starting_question

    def record_assistant_turn(self, text: str) -> None:
        self.memory.record_turn(
            user_text="",
            assistant_text=text,
            turn_index=self.state.turn_index,
            analysis_label=self.state.last_analysis_label,
        )

    async def stream_turn(self, user_text: str) -> AsyncGenerator[str, None]:
        turn_index = self.state.turn_index + 1
        facts = self.fact_extractor.extract(user_text, turn_index=turn_index)
        self.memory.update_facts(facts)
        analysis = self.analyzer.analyze(
            user_text,
            scenario=self.scenario,
            state=self.state,
            extracted_facts=facts,
        )
        action = self.policy.decide(analysis, scenario=self.scenario, state=self.state)
        self.state = self.state_controller.apply_turn(self.state, scenario=self.scenario, analysis=analysis)
        self.memory.memory.current_phase_id = self.state.current_phase_id
        self.memory.memory.last_repair_reason = action.reason if action.action != PolicyAction.GENERATE else None
        await self.evaluator.after_user_turn(scenario=self.scenario, state=self.state, analysis=analysis)

        if action.action == PolicyAction.GENERATE:
            assistant_text = ""
            system_prompt, messages = self.prompt_builder.build(
                scenario=self.scenario,
                memory=self.memory.memory,
                state=self.state,
                user_text=user_text,
                repair_action=action,
            )
            async for chunk in self.llm.chat_stream(
                messages,
                system_prompt=system_prompt,
                max_tokens=settings.llm_max_tokens,
            ):
                assistant_text += chunk
                yield chunk
        else:
            assistant_text = self.policy.repair_text(
                action,
                scenario=self.scenario,
                state=self.state,
                analysis=analysis,
            )
            for chunk in _chunk_text(assistant_text):
                yield chunk

        self.memory.record_turn(
            user_text=user_text,
            assistant_text=assistant_text,
            turn_index=self.state.turn_index,
            analysis_label=analysis.label,
        )
        await self.evaluator.after_assistant_turn(
            scenario=self.scenario,
            state=self.state,
            assistant_text=assistant_text,
        )
        self.last_output = OrchestratorOutput(
            assistant_text=assistant_text,
            analysis=analysis,
            repair_action=action,
            dialogue_state=self.state,
            memory=self.memory.memory,
        )
        logger.info(
            "Hybrid turn completed scenario=%s phase=%s label=%s action=%s",
            self.scenario.scenario_id,
            self.state.current_phase_id,
            analysis.label.value,
            action.action.value,
        )

    def lesson_state(self, *, session_id: int) -> LessonStateRead:
        phase = self.scenario.current_or_first_phase(self.state.current_phase_id)
        completed = len(self.state.completed_phase_ids)
        total = max(1, len(self.scenario.phases))
        progress = LessonProgressSummary(
            completed=min(completed, total),
            total=total,
            percent=min(100, int((completed / total) * 100)),
        )
        expected = phase.expected_intents or self.scenario.expected_intents[:3] or [phase.objective]
        matched = list(self.state.completed_phase_ids)
        missing = [item for item in expected if item not in matched]
        return LessonStateRead(
            lesson_id=f"hybrid-{self.scenario.scenario_id}",
            session_id=session_id,
            scenario_id=int(self.scenario.scenario_id) if str(self.scenario.scenario_id).isdigit() else 0,
            topic=self.scenario.title,
            assigned_task=self.scenario.objective,
            persona=self.scenario.ai_role,
            lesson_goals=[phase.objective for phase in self.scenario.phases] or [self.scenario.objective],
            status="completed" if self.state.should_end else "active",
            current_question=phase.starting_question,
            current_objective=LessonObjectiveState(
                objective_id=phase.phase_id,
                goal=phase.objective,
                main_question=phase.starting_question,
                expected_points=expected,
                matched_points=matched,
                missing_points=missing,
                turns_taken=self.state.turn_index,
                remaining_follow_ups=max(0, 2 - self.state.repair_count),
                status="completed" if self.state.should_end else "active",
            ),
            progress=progress,
            should_end=self.state.should_end,
            end_reason=self.state.end_reason,
            completion_message="Nice work. You completed this practice conversation." if self.state.should_end else None,
            suggested_responses=[],
        )


def _chunk_text(text: str, chunk_size: int = 48) -> list[str]:
    words = text.split()
    if not words:
        return []
    chunks: list[str] = []
    current = ""
    for word in words:
        candidate = f"{current} {word}".strip()
        if current and len(candidate) > chunk_size:
            chunks.append(f"{current} ")
            current = word
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks

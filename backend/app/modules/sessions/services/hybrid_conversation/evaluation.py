from __future__ import annotations

from typing import Protocol

from app.modules.sessions.services.hybrid_conversation.schemas import DialogueState, ScenarioDefinition, TurnAnalysis


class PostTurnEvaluationHook(Protocol):
    async def after_user_turn(
        self,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        analysis: TurnAnalysis,
    ) -> None:
        ...

    async def after_assistant_turn(
        self,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        assistant_text: str,
    ) -> None:
        ...


class NoOpEvaluationHook:
    """Placeholder hook for future relevance, pronunciation, grammar, and fluency scoring."""

    async def after_user_turn(
        self,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        analysis: TurnAnalysis,
    ) -> None:
        return None

    async def after_assistant_turn(
        self,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        assistant_text: str,
    ) -> None:
        return None

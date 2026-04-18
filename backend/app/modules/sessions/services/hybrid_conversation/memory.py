from __future__ import annotations

from app.modules.sessions.services.hybrid_conversation.schemas import DialogueTurn, MemoryFact, SessionMemory


class SessionMemoryManager:
    """Maintains bounded short-term memory for one realtime practice session."""

    def __init__(
        self,
        memory: SessionMemory,
        *,
        max_facts: int,
        recent_turn_limit: int,
        summary_max_chars: int,
    ):
        self.memory = memory
        self.max_facts = max(1, int(max_facts))
        self.recent_turn_limit = max(1, int(recent_turn_limit))
        self.summary_max_chars = max(80, int(summary_max_chars))

    def update_facts(self, facts: list[MemoryFact]) -> None:
        for fact in facts:
            self._upsert_fact(fact)
        self._prune_facts()
        self._refresh_fact_indexes()

    def record_turn(
        self,
        *,
        user_text: str,
        assistant_text: str | None,
        turn_index: int,
        analysis_label=None,
    ) -> None:
        self.memory.recent_turns.append(
            DialogueTurn(
                turn_index=turn_index,
                user_text=user_text.strip(),
                assistant_text=assistant_text.strip() if assistant_text else None,
                analysis_label=analysis_label,
            )
        )
        if len(self.memory.recent_turns) > self.recent_turn_limit:
            self.memory.recent_turns = self.memory.recent_turns[-self.recent_turn_limit :]
        self._update_summary(user_text=user_text, assistant_text=assistant_text)

    def compact_export(self) -> dict[str, str]:
        facts = [
            f"{fact.key}: {fact.value}"
            for fact in sorted(
                self.memory.facts,
                key=lambda item: (item.relevance_to_scenario, item.confidence, item.source_turn_index),
                reverse=True,
            )
            if fact.confidence >= 0.45
        ]
        recent = []
        for turn in self.memory.recent_turns[-self.recent_turn_limit :]:
            recent.append(f"User: {turn.user_text}")
            if turn.assistant_text:
                recent.append(f"AI: {turn.assistant_text}")
        return {
            "facts": "; ".join(facts),
            "summary": self.memory.recent_dialogue_summary[: self.summary_max_chars],
            "recent_turns": "\n".join(recent),
            "phase": self.memory.current_phase_id,
            "objective": self.memory.current_objective,
        }

    def _upsert_fact(self, fact: MemoryFact) -> None:
        normalized_key = fact.key.strip().lower()
        normalized_value = fact.value.strip().lower()
        if not normalized_key or not normalized_value:
            return

        fact = fact.model_copy(update={"key": normalized_key, "value": normalized_value})
        for index, existing in enumerate(self.memory.facts):
            if existing.key != normalized_key:
                continue
            if fact.confidence >= existing.confidence - 0.08 or fact.source_turn_index >= existing.source_turn_index:
                self.memory.facts[index] = existing.model_copy(
                    update={
                        "value": normalized_value,
                        "confidence": max(existing.confidence, fact.confidence),
                        "source_turn_index": max(existing.source_turn_index, fact.source_turn_index),
                        "relevance_to_scenario": max(existing.relevance_to_scenario, fact.relevance_to_scenario),
                    }
                )
            return
        self.memory.facts.append(fact)

    def _prune_facts(self) -> None:
        if len(self.memory.facts) <= self.max_facts:
            return
        self.memory.facts = sorted(
            self.memory.facts,
            key=lambda fact: (fact.relevance_to_scenario, fact.confidence, fact.source_turn_index),
            reverse=True,
        )[: self.max_facts]

    def _refresh_fact_indexes(self) -> None:
        self.memory.user_preferences = {
            fact.key: fact.value for fact in self.memory.facts if fact.category == "preference"
        }
        self.memory.emotional_context = {
            fact.key: fact.value for fact in self.memory.facts if fact.category == "emotion"
        }

    def _update_summary(self, *, user_text: str, assistant_text: str | None) -> None:
        fragment = f"User said: {user_text.strip()}"
        if assistant_text:
            fragment = f"{fragment} AI replied: {assistant_text.strip()}"
        combined = " ".join(part for part in [self.memory.recent_dialogue_summary, fragment] if part)
        if len(combined) > self.summary_max_chars:
            combined = combined[-self.summary_max_chars :].lstrip()
        self.memory.recent_dialogue_summary = combined

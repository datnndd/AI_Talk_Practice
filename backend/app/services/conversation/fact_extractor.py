from __future__ import annotations

import re

from app.services.conversation.schemas import MemoryFact


_EMOTION_WORDS = {
    "afraid",
    "angry",
    "anxious",
    "concerned",
    "confused",
    "excited",
    "happy",
    "nervous",
    "sad",
    "scared",
    "stressed",
    "tired",
    "worried",
}


def _clean_value(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip(" .,!?:;\"'")).lower()


class RuleBasedFactExtractor:
    """Extracts small, reusable learner facts without an LLM dependency."""

    def extract(self, text: str, *, turn_index: int) -> list[MemoryFact]:
        clean = " ".join((text or "").strip().split())
        if not clean:
            return []

        facts: list[MemoryFact] = []
        facts.extend(self._extract_profession(clean, turn_index))
        facts.extend(self._extract_preferences(clean, turn_index))
        facts.extend(self._extract_concerns(clean, turn_index))
        facts.extend(self._extract_needs(clean, turn_index))
        facts.extend(self._extract_context(clean, turn_index))
        return self._dedupe(facts)

    def _extract_profession(self, text: str, turn_index: int) -> list[MemoryFact]:
        patterns = [
            r"\b(?:i am|i'm)\s+(?:a|an)\s+([a-zA-Z][a-zA-Z\s-]{1,40})",
            r"\bmy job is\s+([a-zA-Z][a-zA-Z\s-]{1,40})",
            r"\bi work as\s+(?:a|an)?\s*([a-zA-Z][a-zA-Z\s-]{1,40})",
        ]
        facts: list[MemoryFact] = []
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = _clean_value(match.group(1))
                first = value.split(" ", 1)[0]
                if not value or first in _EMOTION_WORDS:
                    continue
                facts.append(
                    MemoryFact(
                        key="profession",
                        value=value,
                        category="profile",
                        confidence=0.82,
                        source_turn_index=turn_index,
                        relevance_to_scenario=0.65,
                    )
                )
        return facts

    def _extract_preferences(self, text: str, turn_index: int) -> list[MemoryFact]:
        facts: list[MemoryFact] = []
        for match in re.finditer(r"\bi\s+(?:like|love|prefer|enjoy)\s+([^,.!?;]+)", text, flags=re.IGNORECASE):
            value = _clean_value(match.group(1))
            if value:
                facts.append(
                    MemoryFact(
                        key="likes",
                        value=value,
                        category="preference",
                        confidence=0.78,
                        source_turn_index=turn_index,
                        relevance_to_scenario=0.35,
                    )
                )
        return facts

    def _extract_concerns(self, text: str, turn_index: int) -> list[MemoryFact]:
        facts: list[MemoryFact] = []
        pattern = r"\bi(?:'m| am| feel)?\s*(nervous|worried|anxious|concerned|stressed|confused)(?:\s+about\s+([^,.!?;]+))?"
        for match in re.finditer(pattern, text, flags=re.IGNORECASE):
            emotion = _clean_value(match.group(1))
            topic = _clean_value(match.group(2) or "")
            value = f"{emotion} about {topic}" if topic else emotion
            facts.append(
                MemoryFact(
                    key="concern",
                    value=value,
                    category="emotion",
                    confidence=0.8,
                    source_turn_index=turn_index,
                    relevance_to_scenario=0.55,
                )
            )
        return facts

    def _extract_needs(self, text: str, turn_index: int) -> list[MemoryFact]:
        facts: list[MemoryFact] = []
        patterns = [
            r"\bi need\s+([^,.!?;]+)",
            r"\bi want to\s+([^,.!?;]+)",
            r"\bi have to\s+([^,.!?;]+)",
        ]
        for pattern in patterns:
            for match in re.finditer(pattern, text, flags=re.IGNORECASE):
                value = _clean_value(match.group(1))
                if value:
                    facts.append(
                        MemoryFact(
                            key="need",
                            value=value,
                            category="goal",
                            confidence=0.76,
                            source_turn_index=turn_index,
                            relevance_to_scenario=0.8,
                        )
                    )
        return facts

    def _extract_context(self, text: str, turn_index: int) -> list[MemoryFact]:
        facts: list[MemoryFact] = []
        match = re.search(r"\bi(?:'m| am)\s+here\s+for\s+([^,.!?;]+)", text, flags=re.IGNORECASE)
        if match:
            facts.append(
                MemoryFact(
                    key="context",
                    value=_clean_value(match.group(1)),
                    category="context",
                    confidence=0.72,
                    source_turn_index=turn_index,
                    relevance_to_scenario=0.6,
                )
            )
        return facts

    def _dedupe(self, facts: list[MemoryFact]) -> list[MemoryFact]:
        deduped: dict[tuple[str, str], MemoryFact] = {}
        for fact in facts:
            deduped[(fact.key, fact.value)] = fact
        return list(deduped.values())

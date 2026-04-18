from __future__ import annotations

import re

from app.modules.sessions.services.hybrid_conversation.schemas import DialogueState, MemoryFact, ScenarioDefinition, TurnAnalysis, TurnLabel


STOPWORDS = {
    "a",
    "about",
    "an",
    "and",
    "are",
    "can",
    "do",
    "for",
    "from",
    "how",
    "i",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "please",
    "the",
    "this",
    "to",
    "what",
    "with",
    "you",
}
NONSENSE_MARKERS = {"asdf", "qwer", "zxcv", "hjkl", "blahblah", "lorem"}
ORDERING_SCENARIO_MARKERS = {
    "barista",
    "cafe",
    "coffee",
    "customer",
    "drink",
    "food",
    "menu",
    "morning",
    "order",
    "restaurant",
}
ORDERING_ANSWER_MARKERS = {
    "americano",
    "bagel",
    "burger",
    "cappuccino",
    "coffee",
    "croissant",
    "drip",
    "espresso",
    "food",
    "frappe",
    "hot",
    "iced",
    "latte",
    "macchiato",
    "medium",
    "mocha",
    "milk",
    "muffin",
    "oat",
    "order",
    "please",
    "sandwich",
    "small",
    "tea",
    "water",
}


def _tokens(text: str) -> set[str]:
    return {
        token
        for token in re.findall(r"[a-zA-Z']+", text.lower())
        if len(token) > 2 and token not in STOPWORDS
    }


class TopicAnalyzer:
    """Lightweight deterministic turn analysis for topic control."""

    def __init__(self, *, on_topic_threshold: float = 0.28, partial_threshold: float = 0.12):
        self.on_topic_threshold = on_topic_threshold
        self.partial_threshold = partial_threshold

    def analyze(
        self,
        text: str,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        extracted_facts: list[MemoryFact],
    ) -> TurnAnalysis:
        clean = " ".join((text or "").strip().split())
        labels: list[TurnLabel] = []

        if self._is_help_request(clean):
            labels.append(TurnLabel.HELP_REQUEST)
        if self._is_clarification_request(clean):
            labels.append(TurnLabel.CLARIFICATION_REQUEST)
        scenario_tokens = self._scenario_tokens(scenario, state)
        turn_tokens = _tokens(clean)
        is_domain_slot_answer = self._is_domain_slot_answer(
            turn_tokens,
            scenario_tokens,
            scenario=scenario,
            clean=clean,
        )
        relevance = self._relevance_score(
            turn_tokens,
            scenario_tokens,
            clean,
            domain_slot_answer=is_domain_slot_answer,
        )
        contains_fact = bool(extracted_facts)
        contains_direct_answer = (
            relevance >= self.on_topic_threshold
            or is_domain_slot_answer
            or self._has_direct_answer_signal(clean)
        )

        if self._is_nonsense(clean):
            labels.append(TurnLabel.NONSENSE)
        elif self._is_too_short(clean) and not is_domain_slot_answer:
            labels.append(TurnLabel.TOO_SHORT)

        if not any(label in labels for label in (TurnLabel.HELP_REQUEST, TurnLabel.CLARIFICATION_REQUEST, TurnLabel.NONSENSE, TurnLabel.TOO_SHORT)):
            if relevance >= self.on_topic_threshold:
                labels.append(TurnLabel.ON_TOPIC)
            elif relevance >= self.partial_threshold or contains_fact:
                labels.append(TurnLabel.PARTIALLY_ON_TOPIC)
            else:
                labels.append(TurnLabel.OFF_TOPIC)

        primary = labels[0] if labels else TurnLabel.OFF_TOPIC
        if TurnLabel.NONSENSE in labels:
            primary = TurnLabel.NONSENSE
        elif TurnLabel.HELP_REQUEST in labels:
            primary = TurnLabel.HELP_REQUEST
        elif TurnLabel.CLARIFICATION_REQUEST in labels:
            primary = TurnLabel.CLARIFICATION_REQUEST
        elif TurnLabel.TOO_SHORT in labels:
            primary = TurnLabel.TOO_SHORT
        elif TurnLabel.ON_TOPIC in labels:
            primary = TurnLabel.ON_TOPIC
        elif TurnLabel.PARTIALLY_ON_TOPIC in labels:
            primary = TurnLabel.PARTIALLY_ON_TOPIC

        return TurnAnalysis(
            text=clean,
            label=primary,
            labels=labels,
            relevance_score=relevance,
            contains_useful_personal_fact=contains_fact,
            contains_direct_answer=contains_direct_answer,
            contains_clarification_request=TurnLabel.CLARIFICATION_REQUEST in labels,
            extracted_fact_keys=[fact.key for fact in extracted_facts],
            reason=self._reason(primary, relevance, contains_fact),
        )

    def _scenario_tokens(self, scenario: ScenarioDefinition, state: DialogueState) -> set[str]:
        current_phase = scenario.current_or_first_phase(state.current_phase_id)
        chunks = [
            scenario.title,
            scenario.description,
            scenario.objective,
            current_phase.objective,
            current_phase.starting_question,
            " ".join(scenario.allowed_topic_boundaries),
            " ".join(scenario.expected_intents),
            " ".join(scenario.target_vocabulary),
            " ".join(scenario.target_functions),
        ]
        return _tokens(" ".join(chunks))

    def _relevance_score(
        self,
        turn_tokens: set[str],
        scenario_tokens: set[str],
        clean: str,
        *,
        domain_slot_answer: bool,
    ) -> float:
        if not clean:
            return 0.0
        overlap = len(turn_tokens & scenario_tokens)
        base = overlap / max(4, min(len(scenario_tokens) or 1, 16))
        lowered = clean.lower()
        if domain_slot_answer:
            base += 0.35
        if "help" in lowered and any(word in lowered for word in ("document", "draft", "write", "writing", "work")):
            base += 0.45
        if any(word in lowered for word in ("deadline", "interview", "order", "travel", "support")):
            base += 0.15
        return min(1.0, base)

    def _is_help_request(self, text: str) -> bool:
        lowered = text.lower()
        return any(phrase in lowered for phrase in ("give me a hint", "can you help", "what should i say", "example"))

    def _is_clarification_request(self, text: str) -> bool:
        lowered = text.lower().strip()
        return lowered in {"what do you mean", "what do you mean?", "can you repeat", "can you repeat?"} or (
            "what" in lowered and "mean" in lowered
        )

    def _is_nonsense(self, text: str) -> bool:
        lowered = text.lower()
        tokens = _tokens(lowered)
        if not text:
            return False
        if any(marker in lowered for marker in NONSENSE_MARKERS):
            return True
        if re.fullmatch(r"[^a-zA-Z0-9]+", text):
            return True
        return bool(tokens) and all(len(set(token)) <= 2 and len(token) >= 4 for token in tokens)

    def _is_too_short(self, text: str) -> bool:
        return 0 < len(_tokens(text)) <= 1

    def _has_direct_answer_signal(self, text: str) -> bool:
        lowered = text.lower()
        return any(phrase in lowered for phrase in ("i need", "i want", "i would like", "i have to", "i'm here for"))

    def _is_domain_slot_answer(
        self,
        turn_tokens: set[str],
        scenario_tokens: set[str],
        *,
        scenario: ScenarioDefinition,
        clean: str,
    ) -> bool:
        if not turn_tokens:
            return False

        if turn_tokens & scenario_tokens:
            return True

        scenario_text = " ".join(
            [
                scenario.title,
                scenario.description,
                scenario.objective,
                scenario.ai_role,
                scenario.user_role,
                " ".join(scenario.allowed_topic_boundaries),
                " ".join(scenario.target_vocabulary),
                " ".join(scenario.target_functions),
            ]
        )
        scenario_marker_tokens = _tokens(scenario_text)
        is_ordering_scenario = bool(scenario_marker_tokens & ORDERING_SCENARIO_MARKERS)
        if not is_ordering_scenario:
            return False

        lowered = clean.lower()
        has_ordering_answer = bool(turn_tokens & ORDERING_ANSWER_MARKERS)
        polite_short_order = any(phrase in lowered for phrase in ("i'd like", "i would like", "can i get", "please"))
        return has_ordering_answer or polite_short_order

    def _reason(self, label: TurnLabel, relevance: float, contains_fact: bool) -> str:
        if contains_fact and label == TurnLabel.PARTIALLY_ON_TOPIC:
            return "contains useful learner fact but does not answer the active scenario need"
        return f"{label.value} relevance={relevance:.2f}"

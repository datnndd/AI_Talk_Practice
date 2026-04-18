from __future__ import annotations

import json
import logging
import re

from pydantic import BaseModel, Field

from app.infra.contracts import LLMBase, Message
from app.modules.sessions.services.hybrid_conversation.analyzer import TopicAnalyzer
from app.modules.sessions.services.hybrid_conversation.schemas import DialogueState, MemoryFact, ScenarioDefinition, TurnAnalysis, TurnLabel

logger = logging.getLogger(__name__)


class LLMExtractedFact(BaseModel):
    key: str
    value: str
    category: str
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    relevance_to_scenario: float = Field(default=0.5, ge=0.0, le=1.0)


class LLMTurnAnalysisPayload(BaseModel):
    label: TurnLabel
    relevance_score: float = Field(ge=0.0, le=1.0)
    confidence: float = Field(default=0.75, ge=0.0, le=1.0)
    contains_direct_answer: bool = False
    intent: str | None = None
    useful_facts: list[LLMExtractedFact] = Field(default_factory=list)
    repair_reason: str = ""


class LLMTurnAnalysisService:
    """Rule-first turn analysis with optional LLM enrichment for ambiguous turns."""

    def __init__(
        self,
        *,
        llm: LLMBase,
        analyzer: TopicAnalyzer | None = None,
        enable_llm_relevance: bool,
        enable_llm_fact_extraction: bool,
        max_tokens: int = 360,
    ):
        self.llm = llm
        self.analyzer = analyzer or TopicAnalyzer()
        self.enable_llm_relevance = enable_llm_relevance
        self.enable_llm_fact_extraction = enable_llm_fact_extraction
        self.max_tokens = max_tokens

    async def analyze(
        self,
        text: str,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        rule_facts: list[MemoryFact],
    ) -> tuple[TurnAnalysis, list[MemoryFact]]:
        rule_analysis = self.analyzer.analyze(
            text,
            scenario=scenario,
            state=state,
            extracted_facts=rule_facts,
        )
        if not self._should_call_llm(rule_analysis, rule_facts):
            return rule_analysis, rule_facts

        try:
            payload = await self._call_llm(text, scenario=scenario, state=state, rule_analysis=rule_analysis)
        except Exception:
            logger.exception("LLM turn analysis failed; falling back to rule analysis")
            return rule_analysis, rule_facts

        llm_facts = [
            MemoryFact(
                key=fact.key,
                value=fact.value,
                category=fact.category,
                confidence=fact.confidence,
                relevance_to_scenario=fact.relevance_to_scenario,
                source_turn_index=state.turn_index + 1,
            )
            for fact in payload.useful_facts
        ]
        facts = rule_facts + llm_facts if self.enable_llm_fact_extraction else rule_facts
        analysis = rule_analysis.model_copy(
            update={
                "label": payload.label,
                "labels": list(dict.fromkeys([payload.label, *rule_analysis.labels])),
                "relevance_score": payload.relevance_score,
                "confidence": payload.confidence,
                "intent": payload.intent,
                "contains_direct_answer": payload.contains_direct_answer,
                "contains_useful_personal_fact": bool(facts),
                "extracted_fact_keys": list(dict.fromkeys([*rule_analysis.extracted_fact_keys, *[fact.key for fact in facts]])),
                "reason": payload.repair_reason or rule_analysis.reason,
            }
        )
        return analysis, facts

    def _should_call_llm(self, analysis: TurnAnalysis, facts: list[MemoryFact]) -> bool:
        if not (self.enable_llm_relevance or self.enable_llm_fact_extraction):
            return False
        if self.enable_llm_relevance and analysis.label in {
            TurnLabel.PARTIALLY_ON_TOPIC,
            TurnLabel.OFF_TOPIC,
        }:
            return True
        near_partial = abs(analysis.relevance_score - self.analyzer.partial_threshold) <= 0.08
        near_on_topic = abs(analysis.relevance_score - self.analyzer.on_topic_threshold) <= 0.08
        if self.enable_llm_relevance and (near_partial or near_on_topic):
            return True
        return self.enable_llm_fact_extraction and not facts and analysis.label not in {
            TurnLabel.NONSENSE,
            TurnLabel.TOO_SHORT,
        }

    async def _call_llm(
        self,
        text: str,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        rule_analysis: TurnAnalysis,
    ) -> LLMTurnAnalysisPayload:
        system_prompt = self._system_prompt(scenario=scenario, state=state, rule_analysis=rule_analysis)
        chunks = []
        async for chunk in self.llm.chat_stream(
            [Message(role="user", content=text.strip())],
            system_prompt=system_prompt,
            max_tokens=self.max_tokens,
        ):
            chunks.append(chunk)
        raw = "".join(chunks).strip()
        return LLMTurnAnalysisPayload.model_validate(_parse_json_object(raw))

    def _system_prompt(
        self,
        *,
        scenario: ScenarioDefinition,
        state: DialogueState,
        rule_analysis: TurnAnalysis,
    ) -> str:
        phase = scenario.current_or_first_phase(state.current_phase_id)
        return "\n".join(
            [
                "Analyze one learner utterance for an English speaking practice scenario.",
                "Return only one JSON object. Do not include markdown.",
                f"Scenario: {scenario.title}",
                f"Objective: {scenario.objective}",
                f"Current phase: {phase.title} - {phase.objective}",
                f"Allowed topic boundaries: {'; '.join(scenario.allowed_topic_boundaries[:8])}",
                f"Rule label: {rule_analysis.label.value}",
                f"Rule relevance score: {rule_analysis.relevance_score:.2f}",
                "JSON schema: {",
                '  "label": "on_topic|partially_on_topic|off_topic|nonsense|help_request|too_short|clarification_request",',
                '  "relevance_score": 0.0,',
                '  "confidence": 0.0,',
                '  "contains_direct_answer": true,',
                '  "intent": "short intent label",',
                '  "useful_facts": [{"key":"need","value":"help writing a report","category":"goal","confidence":0.8,"relevance_to_scenario":0.9}],',
                '  "repair_reason": "short reason"',
                "}",
            ]
        )


def _parse_json_object(raw: str) -> dict:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, flags=re.DOTALL)
    if fenced:
        raw = fenced.group(1)
    else:
        start = raw.find("{")
        end = raw.rfind("}")
        if start >= 0 and end >= start:
            raw = raw[start : end + 1]
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError("Invalid LLM analysis JSON") from exc
    if not isinstance(parsed, dict):
        raise ValueError("LLM analysis response must be a JSON object")
    return parsed

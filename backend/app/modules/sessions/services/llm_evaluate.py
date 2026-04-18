from typing import Dict
from pydantic import BaseModel, Field

from app.infra.llm.openai_llm import OpenAILLM
from app.modules.sessions.models.session import Session

class EvalScores(BaseModel):
    grammar: int = Field(1, ge=1, le=5)
    vocabulary: int = Field(1, ge=1, le=5)
    pronunciation: int = Field(1, ge=1, le=5)

class LLM_EvaluateResponse(BaseModel):
    scores: EvalScores
    feedback: Dict[str, str]

async def llm_evaluate(session: Session, llm: OpenAILLM = OpenAILLM()) -> LLM_EvaluateResponse:
    prompt = f"""Evaluate speaking session transcript:

Transcript: {session.transcript}

Audio summary: {session.audio_metadata or 'No audio data'}

Scenario: {session.scenario.title}

Score grammar, vocabulary, pronunciation on 1-5 scale.
Provide structured feedback.

JSON:"""
    response = await llm.chat([{"role": "user", "content": prompt}], max_tokens=500)
    return LLM_EvaluateResponse.model_validate_json(response)
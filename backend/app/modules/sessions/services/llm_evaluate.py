from __future__ import annotations

from pydantic import BaseModel, Field

from app.modules.sessions.models.session import Session


class EvalScores(BaseModel):
    grammar: int = Field(ge=1, le=5)
    vocabulary: int = Field(ge=1, le=5)
    pronunciation: int = Field(ge=1, le=5)


class LLM_EvaluateResponse(BaseModel):
    overall_score: float
    scores: EvalScores
    feedback: str


async def llm_evaluate(session: Session, llm=None) -> LLM_EvaluateResponse:
    """Deprecated wrapper.

    Full session assessment now lives in SessionFinalEvaluationService. This
    adapter returns already-stored score data when legacy callers still import
    this function.
    """
    score = getattr(session, "score", None)
    if score is None:
        return LLM_EvaluateResponse(
            overall_score=0.0,
            scores=EvalScores(grammar=1, vocabulary=1, pronunciation=1),
            feedback="No stored final assessment is available for this session.",
        )

    return LLM_EvaluateResponse(
        overall_score=float(score.overall_score or 0.0),
        scores=EvalScores(
            grammar=_score_10_to_5(score.avg_grammar),
            vocabulary=_score_10_to_5(score.avg_vocabulary),
            pronunciation=_score_10_to_5(score.avg_pronunciation),
        ),
        feedback=score.feedback_summary or "Final assessment is available in the session score.",
    )


def _score_10_to_5(value: float | None) -> int:
    if value is None:
        return 1
    return max(1, min(5, round(float(value) / 2)))

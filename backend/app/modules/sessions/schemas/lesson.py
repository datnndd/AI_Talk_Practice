from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LessonHintRead(BaseModel):
    lesson_id: str
    objective_id: str
    question: str | None = None
    hints: list[str] = Field(default_factory=list)
    analysis_vi: str = ""
    answer_strategy_vi: str = ""
    keywords: list[str] = Field(default_factory=list)
    sample_answers: list[str] = Field(default_factory=list)
    sample_answer: str = ""
    sample_answer_easy: str = ""
    cached: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

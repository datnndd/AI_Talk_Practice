from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class LessonHintSeed(BaseModel):
    focus: str
    grammar: str | None = None
    max_length: int = Field(default=3, ge=1, le=6)


class LessonObjective(BaseModel):
    objective_id: str
    goal: str
    main_question: str
    follow_up_questions: list[str] = Field(default_factory=list)
    expected_points: list[str] = Field(default_factory=list)
    hint_seed: LessonHintSeed


class LessonPackage(BaseModel):
    lesson_id: str
    scenario_id: int
    scenario: str
    level: str
    persona: str
    objectives: list[LessonObjective] = Field(default_factory=list)


class LessonProgressState(BaseModel):
    current_objective_index: int = 0
    attempts_by_objective: dict[str, int] = Field(default_factory=dict)
    follow_up_index_by_objective: dict[str, int] = Field(default_factory=dict)
    completed_objective_ids: list[str] = Field(default_factory=list)
    last_question: str | None = None
    status: str = Field(default="active", pattern=r"^(active|completed)$")
    should_end: bool = False
    end_reason: str | None = None
    completion_message: str | None = None


class LessonObjectiveState(BaseModel):
    objective_id: str
    goal: str
    main_question: str
    expected_points: list[str] = Field(default_factory=list)
    matched_points: list[str] = Field(default_factory=list)
    missing_points: list[str] = Field(default_factory=list)
    turns_taken: int = 0
    remaining_follow_ups: int = 0
    status: str = Field(default="active", pattern=r"^(active|completed)$")


class LessonProgressSummary(BaseModel):
    completed: int
    total: int
    percent: int = Field(ge=0, le=100)


class LessonStateRead(BaseModel):
    lesson_id: str
    session_id: int
    scenario_id: int
    topic: str
    assigned_task: str
    persona: str
    status: str = Field(pattern=r"^(active|completed)$")
    current_question: str
    current_objective: LessonObjectiveState
    progress: LessonProgressSummary
    should_end: bool = False
    end_reason: str | None = None
    completion_message: str | None = None
    suggested_responses: list[str] = Field(default_factory=list)


class LessonGenerateRequest(BaseModel):
    session_id: int
    scenario_id: int
    level: str | None = None
    regenerate: bool = False


class LessonNextQuestionRequest(BaseModel):
    session_id: int
    lesson_id: str
    user_answer: str = Field(min_length=1)


class LessonHintRequest(BaseModel):
    session_id: int
    lesson_id: str
    objective_id: str | None = None
    user_last_answer: str | None = None


class LessonHintRead(BaseModel):
    lesson_id: str
    objective_id: str
    analysis_vi: str
    answer_strategy_vi: str
    keywords: list[str] = Field(default_factory=list)
    sample_answer: str
    sample_answer_easy: str
    cached: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)

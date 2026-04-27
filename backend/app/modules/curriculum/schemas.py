from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ExerciseType = Literal[
    "vocab_pronunciation",
    "cloze_dictation",
    "sentence_pronunciation",
    "interactive_conversation",
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LearningLevelBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    order_index: int = Field(default=0, ge=0)
    is_active: bool = True


class LearningLevelCreate(LearningLevelBase):
    pass


class LearningLevelUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class LessonBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    order_index: int = Field(default=0, ge=0)
    estimated_minutes: int | None = Field(default=None, ge=1, le=300)
    xp_reward: int = Field(default=50, ge=0)
    coin_reward: int = Field(default=0, ge=0)
    is_active: bool = True


class LessonCreate(LessonBase):
    level_id: int


class LessonUpdate(BaseModel):
    level_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=0)
    estimated_minutes: int | None = Field(default=None, ge=1, le=300)
    xp_reward: int | None = Field(default=None, ge=0)
    coin_reward: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class LessonExerciseBase(BaseModel):
    type: ExerciseType
    title: str = Field(min_length=1, max_length=200)
    order_index: int = Field(default=0, ge=0)
    content: dict[str, Any] = Field(default_factory=dict)
    pass_score: float = Field(default=80, ge=0, le=100)
    is_required: bool = True
    is_active: bool = True

    @field_validator("content")
    @classmethod
    def validate_content_shape(cls, value: dict[str, Any], info):
        exercise_type = info.data.get("type")
        if not exercise_type:
            return value
        if exercise_type == "vocab_pronunciation":
            if not isinstance(value.get("words"), list) or not value.get("words"):
                raise ValueError("vocab_pronunciation requires content.words")
        elif exercise_type == "cloze_dictation":
            if not value.get("passage") or not isinstance(value.get("blanks"), list) or not value.get("blanks"):
                raise ValueError("cloze_dictation requires content.passage and content.blanks")
        elif exercise_type == "sentence_pronunciation":
            if not value.get("reference_text"):
                raise ValueError("sentence_pronunciation requires content.reference_text")
        elif exercise_type == "interactive_conversation":
            if not value.get("scenario_id"):
                raise ValueError("interactive_conversation requires content.scenario_id")
        return value


class LessonExerciseCreate(LessonExerciseBase):
    lesson_id: int


class LessonExerciseUpdate(BaseModel):
    lesson_id: int | None = None
    type: ExerciseType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    order_index: int | None = Field(default=None, ge=0)
    content: dict[str, Any] | None = None
    pass_score: float | None = Field(default=None, ge=0, le=100)
    is_required: bool | None = None
    is_active: bool | None = None


class ReorderItem(BaseModel):
    id: int
    order_index: int = Field(ge=0)


class ReorderRequest(BaseModel):
    items: list[ReorderItem] = Field(min_length=1)


class DictionaryPreviewRequest(BaseModel):
    words: list[str] = Field(min_length=1)


class DictionaryTermRead(ORMModel):
    id: int | None = None
    word: str
    normalized_word: str
    language: str = "en"
    meaning_vi: str | None = None
    ipa: str | None = None
    audio_url: str | None = None
    source_metadata: dict[str, Any] | None = None


class ProgressSummary(BaseModel):
    status: str = "not_started"
    best_score: float | None = None
    attempt_count: int = 0
    state: dict[str, Any] = Field(default_factory=dict)


class LessonExerciseRead(ORMModel):
    id: int
    lesson_id: int
    type: ExerciseType
    title: str
    order_index: int
    content: dict[str, Any]
    pass_score: float
    is_required: bool
    is_active: bool
    progress: ProgressSummary | None = None
    created_at: datetime
    updated_at: datetime


class LessonRead(ORMModel):
    id: int
    level_id: int
    title: str
    description: str | None = None
    order_index: int
    estimated_minutes: int | None = None
    xp_reward: int
    coin_reward: int
    is_active: bool
    is_locked: bool = False
    progress_status: str = "not_started"
    best_score: float | None = None
    exercises: list[LessonExerciseRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LearningLevelRead(ORMModel):
    id: int
    code: str
    title: str
    description: str | None = None
    order_index: int
    is_active: bool
    lessons: list[LessonRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CurriculumTreeRead(BaseModel):
    levels: list[LearningLevelRead]
    current_lesson_id: int | None = None


class ExerciseAttemptRequest(BaseModel):
    answer: Any | None = None
    audio_base64: str | None = None
    audio_url: str | None = None
    session_id: int | None = None


class ExerciseAttemptRead(ORMModel):
    id: int
    exercise_id: int
    score: float
    passed: bool
    feedback: dict[str, Any] = Field(default_factory=dict)
    progress: ProgressSummary
    lesson_completed: bool = False
    reward: dict[str, Any] | None = None


class StartConversationExerciseRequest(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


class StartConversationExerciseResponse(BaseModel):
    session_id: int
    scenario_id: int
    result_url: str
    metadata: dict[str, Any] = Field(default_factory=dict)

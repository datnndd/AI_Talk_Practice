from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


VALID_LESSON_TYPES = {"shadowing", "definition_choice", "quick_qa"}

LessonType = Literal[
    "shadowing",
    "definition_choice",
    "quick_qa",
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LearningSectionBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    cefr_level: str | None = Field(default=None, max_length=10)
    description: str | None = None
    is_active: bool = True


class LearningSectionCreate(LearningSectionBase):
    pass


class LearningSectionUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    cefr_level: str | None = Field(default=None, max_length=10)
    description: str | None = None
    is_active: bool | None = None


class UnitBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=300)
    xp_reward: int = Field(default=50, ge=0)
    coin_reward: int = Field(default=0, ge=0)
    is_active: bool = True


class UnitCreate(UnitBase):
    section_id: int


class UnitUpdate(BaseModel):
    section_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    estimated_minutes: int | None = Field(default=None, ge=1, le=300)
    xp_reward: int | None = Field(default=None, ge=0)
    coin_reward: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


def _validate_lesson_content(exercise_type: str | None, value: dict[str, Any]) -> dict[str, Any]:
    if not exercise_type:
        return value
    if exercise_type == "shadowing":
        if not value.get("reference_text"):
            raise ValueError("shadowing requires content.reference_text")
        if not value.get("sample_audio_url"):
            raise ValueError("shadowing requires content.sample_audio_url")
    elif exercise_type == "definition_choice":
        options = value.get("options")
        if not value.get("definition_audio_url"):
            raise ValueError("definition_choice requires content.definition_audio_url")
        if not isinstance(options, list) or len(options) != 4:
            raise ValueError("definition_choice requires exactly four content.options")
        correct = [item for item in options if isinstance(item, dict) and item.get("is_correct") is True]
        words = [item.get("word") for item in options if isinstance(item, dict) and item.get("word")]
        if len(correct) != 1:
            raise ValueError("definition_choice requires exactly one correct option")
        if len(words) != len(options):
            raise ValueError("definition_choice options require word")
    elif exercise_type == "quick_qa":
        if not value.get("question_text"):
            raise ValueError("quick_qa requires content.question_text")
        hints = value.get("answer_hints") or []
        if hints and (not isinstance(hints, list) or len(hints) > 3):
            raise ValueError("quick_qa content.answer_hints must contain up to three hints")
    return value



class LessonBase(BaseModel):
    type: LessonType
    title: str = Field(default="", max_length=200)
    order_index: int = Field(default=0, ge=0)
    content: dict[str, Any] = Field(default_factory=dict)
    pass_score: float = Field(default=80, ge=0, le=100)
    is_active: bool = True

    @field_validator("content")
    @classmethod
    def validate_content_shape(cls, value: dict[str, Any], info):
        return _validate_lesson_content(info.data.get("type"), value)


class LessonCreate(LessonBase):
    unit_id: int


class LessonUpdate(BaseModel):
    unit_id: int | None = None
    type: LessonType | None = None
    title: str | None = Field(default=None, min_length=1, max_length=200)
    order_index: int | None = Field(default=None, ge=0)
    content: dict[str, Any] | None = None
    pass_score: float | None = Field(default=None, ge=0, le=100)
    is_active: bool | None = None

    @field_validator("content")
    @classmethod
    def validate_update_content_shape(cls, value: dict[str, Any] | None, info):
        if value is None:
            return value
        return _validate_lesson_content(info.data.get("type"), value)


class ReorderItem(BaseModel):
    id: int
    order_index: int = Field(ge=0)


class ReorderRequest(BaseModel):
    items: list[ReorderItem] = Field(min_length=1)


class ProgressSummary(BaseModel):
    status: str = "not_started"
    best_score: float | None = None
    attempt_count: int = 0
    state: dict[str, Any] = Field(default_factory=dict)


class LessonRead(ORMModel):
    id: int
    unit_id: int
    type: LessonType
    title: str
    order_index: int
    content: dict[str, Any]
    pass_score: float
    is_active: bool
    progress: ProgressSummary | None = None
    created_at: datetime
    updated_at: datetime


class LessonAudioTTSRequest(BaseModel):
    text: str = Field(min_length=1, max_length=5000)
    lesson_id: int | None = None
    voice: str | None = Field(default=None, max_length=100)
    language: str | None = Field(default="en", max_length=20)


class LessonAudioAssetRead(ORMModel):
    id: int
    lesson_id: int | None = None
    source: Literal["tts", "upload"]
    text: str | None = None
    voice: str | None = None
    language: str | None = None
    filename: str
    url: str
    content_type: str
    size_bytes: int
    created_at: datetime
    updated_at: datetime


class UnitRead(ORMModel):
    id: int
    section_id: int
    title: str
    description: str | None = None
    estimated_minutes: int | None = None
    xp_reward: int
    coin_reward: int
    is_active: bool
    is_locked: bool = False
    progress_status: str = "not_started"
    best_score: float | None = None
    completed_lessons: int = 0
    total_lessons: int = 0
    progress_percent: int = 0
    lessons: list[LessonRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LearningSectionRead(ORMModel):
    id: int
    code: str
    title: str
    cefr_level: str | None = None
    description: str | None = None
    is_active: bool
    units: list[UnitRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LearningSectionListResponse(BaseModel):
    items: list[LearningSectionRead]
    total: int
    page: int
    page_size: int


class CurriculumTreeRead(BaseModel):
    sections: list[LearningSectionRead]
    current_unit_id: int | None = None
    current_cefr: str = "A1"


class LessonAttemptRequest(BaseModel):
    answer: Any | None = None
    audio_base64: str | None = None
    audio_url: str | None = None
    session_id: int | None = None


class LessonAttemptRead(ORMModel):
    id: int
    lesson_id: int
    score: float
    passed: bool
    feedback: dict[str, Any] = Field(default_factory=dict)
    progress: ProgressSummary
    unit_completed: bool = False
    reward: dict[str, Any] | None = None

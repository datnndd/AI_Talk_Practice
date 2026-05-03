from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


LessonType = Literal[
    "vocab_pronunciation",
    "cloze_dictation",
    "sentence_pronunciation",
    "interactive_conversation",
    "word_audio_choice",
]


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LearningSectionBase(BaseModel):
    code: str = Field(min_length=1, max_length=50)
    title: str = Field(min_length=1, max_length=200)
    cefr_level: str | None = Field(default=None, max_length=10)
    description: str | None = None
    order_index: int = Field(default=0, ge=0)
    is_active: bool = True


class LearningSectionCreate(LearningSectionBase):
    pass


class LearningSectionUpdate(BaseModel):
    code: str | None = Field(default=None, min_length=1, max_length=50)
    title: str | None = Field(default=None, min_length=1, max_length=200)
    cefr_level: str | None = Field(default=None, max_length=10)
    description: str | None = None
    order_index: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class UnitBase(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = None
    order_index: int = Field(default=0, ge=0)
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
    order_index: int | None = Field(default=None, ge=0)
    estimated_minutes: int | None = Field(default=None, ge=1, le=300)
    xp_reward: int | None = Field(default=None, ge=0)
    coin_reward: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


def _validate_lesson_content(exercise_type: str | None, value: dict[str, Any]) -> dict[str, Any]:
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
    elif exercise_type == "word_audio_choice":
        options = value.get("options")
        if not value.get("prompt_word") or not isinstance(options, list) or len(options) < 2:
            raise ValueError("word_audio_choice requires content.prompt_word and at least two content.options")
        correct = [item for item in options if isinstance(item, dict) and item.get("is_correct") is True]
        words = [item.get("word") for item in options if isinstance(item, dict) and item.get("word")]
        if len(correct) != 1:
            raise ValueError("word_audio_choice requires exactly one correct option")
        if len(words) != len(options):
            raise ValueError("word_audio_choice options require word")
    return value


class LessonBase(BaseModel):
    type: LessonType
    title: str = Field(default="", max_length=200)
    order_index: int = Field(default=0, ge=0)
    content: dict[str, Any] = Field(default_factory=dict)
    pass_score: float = Field(default=80, ge=0, le=100)
    is_required: bool = True
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
    is_required: bool | None = None
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
    is_required: bool
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
    order_index: int
    estimated_minutes: int | None = None
    xp_reward: int
    coin_reward: int
    is_active: bool
    is_locked: bool = False
    progress_status: str = "not_started"
    best_score: float | None = None
    lessons: list[LessonRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class LearningSectionRead(ORMModel):
    id: int
    code: str
    title: str
    cefr_level: str | None = None
    description: str | None = None
    order_index: int
    is_active: bool
    units: list[UnitRead] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


class CurriculumTreeRead(BaseModel):
    sections: list[LearningSectionRead]
    current_unit_id: int | None = None


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


class StartConversationLessonRequest(BaseModel):
    metadata: dict[str, Any] = Field(default_factory=dict)


class StartConversationLessonResponse(BaseModel):
    session_id: int
    scenario_id: int
    result_url: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class DictionaryLookupRead(BaseModel):
    word: str
    language: str = "en"
    definition_language: str = "vi"
    meaning_vi: str | None = None
    ipa: str | None = None
    audio_url: str | None = None
    source: str = "dict.minhqnd.com"
    exists: bool = False
    definitions: list[str] = Field(default_factory=list)

"""
Pydantic schemas for API request/response validation.
"""

from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel, EmailStr, Field


# ── Auth ──

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    display_name: str = Field(min_length=1, max_length=100)
    native_language: str = Field(default="vi", max_length=10)
    target_language: str = Field(default="en", max_length=10)
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    display_name: str
    native_language: str
    target_language: str
    level: str
    created_at: datetime

    class Config:
        from_attributes = True


# ── Scenario ──

class ScenarioCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str
    learning_objectives: str = ""
    ai_system_prompt: str
    category: str = Field(max_length=50)
    difficulty: str = Field(default="medium", pattern="^(easy|medium|hard)$")

class ScenarioUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    learning_objectives: Optional[str] = None
    ai_system_prompt: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    is_active: Optional[bool] = None

class ScenarioResponse(BaseModel):
    id: int
    title: str
    description: str
    learning_objectives: str
    ai_system_prompt: str
    category: str
    difficulty: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Session & Messages ──

class CorrectionResponse(BaseModel):
    original_text: str
    corrected_text: str
    explanation: str
    error_type: str

    class Config:
        from_attributes = True

class MessageScoreResponse(BaseModel):
    pronunciation_score: float
    fluency_score: float
    grammar_score: float
    vocabulary_score: float
    intonation_score: float
    overall_score: float
    mispronounced_words: Optional[Any] = None
    feedback: Optional[str] = None

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    order_index: int
    corrections: List[CorrectionResponse] = []
    score: Optional[MessageScoreResponse] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SessionScoreResponse(BaseModel):
    avg_pronunciation: float
    avg_fluency: float
    avg_grammar: float
    avg_vocabulary: float
    avg_intonation: float
    relevance_score: float
    overall_score: float
    feedback_summary: Optional[str] = None

    class Config:
        from_attributes = True

class SessionListItem(BaseModel):
    id: int
    scenario_title: str
    status: str
    duration_seconds: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    overall_score: Optional[float] = None

class SessionDetailResponse(BaseModel):
    id: int
    scenario_id: int
    scenario_title: str
    status: str
    duration_seconds: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    messages: List[MessageResponse] = []
    score: Optional[SessionScoreResponse] = None

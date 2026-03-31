from datetime import datetime
from typing import Optional, List, Any

from pydantic import BaseModel

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

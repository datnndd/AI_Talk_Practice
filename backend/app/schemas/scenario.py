from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

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

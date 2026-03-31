from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

class OnboardingRequest(BaseModel):
    display_name: str = Field(min_length=1, max_length=100)
    native_language: str = Field(default="vi", max_length=10)
    avatar: Optional[str] = None
    age: Optional[int] = None
    level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    learning_purpose: Optional[str] = None
    main_challenge: Optional[str] = None
    favorite_topics: Optional[str] = None # can be a comma separated string
    daily_goal: Optional[int] = None

class UserResponse(BaseModel):
    id: int
    email: str
    display_name: Optional[str] = None
    native_language: Optional[str] = None
    target_language: Optional[str] = None
    level: Optional[str] = None
    avatar: Optional[str] = None
    age: Optional[int] = None
    learning_purpose: Optional[str] = None
    main_challenge: Optional[str] = None
    favorite_topics: Optional[str] = None
    daily_goal: Optional[int] = None
    is_onboarding_completed: bool
    created_at: datetime

    class Config:
        from_attributes = True

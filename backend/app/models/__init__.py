"""
SQLAlchemy ORM models for AI Talk Practice.

Import order matters for Alembic autogenerate — Base must be imported before
any model so all table definitions are registered on the metadata.
"""

from app.models.user import User
from app.models.scenario import Scenario, ScenarioPromptHistory, ScenarioVariation
from app.models.session import Session
from app.models.message import Message
from app.models.correction import Correction
from app.models.message_score import MessageScore
from app.models.session_score import SessionScore

from app.models.subscription import Subscription
from app.models.achievement import Achievement
from app.models.user_achievement import UserAchievement
from app.models.phoneme_error import PhonemeError
from app.models.word_error import WordError
from app.models.daily_stat import DailyStat


__all__ = [
    "User",
    "Scenario",
    "ScenarioPromptHistory",
    "ScenarioVariation",
    "Session",
    "Message",
    "Correction",
    "MessageScore",
    "SessionScore",
    "Subscription",
    "Achievement",
    "UserAchievement",
    "PhonemeError",
    "WordError",
    "DailyStat",
]

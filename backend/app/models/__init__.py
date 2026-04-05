"""
SQLAlchemy ORM models for AI Talk Practice.

Import order matters for Alembic autogenerate — Base must be imported before
any model so all table definitions are registered on the metadata.
"""

# Users
from app.modules.users.models.user import User
from app.modules.users.models.subscription import Subscription

# Scenarios
from app.modules.scenarios.models import Scenario, ScenarioVariation, ScenarioPromptHistory

# Sessions
from app.modules.sessions.models import (
    Session,
    Message,
    Correction,
    MessageScore,
    SessionScore,
    PhonemeError,
    WordError,
)

# Gamification
from app.modules.gamification.models.achievement import Achievement
from app.modules.gamification.models.user_achievement import UserAchievement
from app.modules.gamification.models.daily_stat import DailyStat

__all__ = [
    "User",
    "Subscription",
    "Scenario",
    "ScenarioVariation",
    "ScenarioPromptHistory",
    "Session",
    "Message",
    "Correction",
    "MessageScore",
    "SessionScore",
    "PhonemeError",
    "WordError",
    "Achievement",
    "UserAchievement",
    "DailyStat",
]

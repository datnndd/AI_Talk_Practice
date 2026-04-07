"""
Central ORM model registry for SQLAlchemy metadata initialization.

Import this module once during startup or scripts so every feature model is
registered on Base.metadata before the ORM is used.
"""

# Users
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User

# Payments
from app.modules.payments.models.payment_transaction import PaymentTransaction
from app.modules.payments.models.payment_webhook_event import PaymentWebhookEvent

# Scenarios
from app.modules.scenarios.models.scenario import (
    Scenario,
    ScenarioPromptHistory,
    ScenarioVariation,
)

# Sessions
from app.modules.sessions.models.correction import Correction
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.message_score import MessageScore
from app.modules.sessions.models.phoneme_error import PhonemeError
from app.modules.sessions.models.session import Session
from app.modules.sessions.models.session_score import SessionScore
from app.modules.sessions.models.word_error import WordError

# Gamification
from app.modules.gamification.models.achievement import Achievement
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.models.user_achievement import UserAchievement

__all__ = [
    "Achievement",
    "Correction",
    "DailyStat",
    "Message",
    "MessageScore",
    "PaymentTransaction",
    "PaymentWebhookEvent",
    "PhonemeError",
    "Scenario",
    "ScenarioPromptHistory",
    "ScenarioVariation",
    "Session",
    "SessionScore",
    "Subscription",
    "User",
    "UserAchievement",
    "WordError",
]

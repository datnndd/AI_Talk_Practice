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
)

# Sessions
from app.modules.sessions.models.correction import Correction
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.session import Session
from app.modules.sessions.models.session_score import SessionScore

# Curriculum
from app.modules.curriculum.models import (
    DictionaryTerm,
    ExerciseAttempt,
    LearningLevel,
    Lesson,
    LessonExercise,
    UserExerciseProgress,
    UserLessonProgress,
)

# Gamification
from app.modules.gamification.models.coin_transaction import CoinTransaction
from app.modules.gamification.models.daily_checkin import DailyCheckin
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.models.gamification_setting import GamificationSetting

# Admin
from app.modules.admin.models.audit_log import AdminAuditLog

# Notifications
from app.modules.notifications.models.notification import Notification, NotificationReadState

__all__ = [
    "AdminAuditLog",
    "CoinTransaction",
    "Correction",
    "DailyCheckin",
    "DailyStat",
    "DictionaryTerm",
    "ExerciseAttempt",
    "GamificationSetting",
    "Message",
    "LearningLevel",
    "Lesson",
    "LessonExercise",
    "Notification",
    "NotificationReadState",
    "PaymentTransaction",
    "PaymentWebhookEvent",
    "Scenario",
    "ScenarioPromptHistory",
    "Session",
    "SessionScore",
    "Subscription",
    "User",
    "UserExerciseProgress",
    "UserLessonProgress",
]

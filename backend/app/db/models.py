"""
Central ORM model registry for SQLAlchemy metadata initialization.

Import this module once during startup or scripts so every feature model is
registered on Base.metadata before the ORM is used.
"""

# Users
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User

# Auth
from app.modules.auth.models.email_otp import EmailOTP

# Payments
from app.modules.payments.models.payment_transaction import PaymentTransaction
from app.modules.payments.models.payment_webhook_event import PaymentWebhookEvent
from app.modules.payments.models.subscription_billing import PromotionCode, SubscriptionPlan

# Characters and scenarios
from app.modules.characters.models.character import Character
from app.modules.scenarios.models.scenario import Scenario

# Sessions
from app.modules.sessions.models.correction import Correction
from app.modules.sessions.models.message import Message
from app.modules.sessions.models.session import Session
from app.modules.sessions.models.session_score import SessionScore

# Curriculum
from app.modules.curriculum.models import (
    DictionaryAudioCache,
    LearningSection,
    Lesson,
    LessonAttempt,
    Unit,
    UserLessonProgress,
    UserUnitProgress,
)

# Gamification
from app.modules.gamification.models.coin_transaction import CoinTransaction
from app.modules.gamification.models.daily_checkin import DailyCheckin
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.models.gamification_setting import GamificationSetting
from app.modules.gamification.models.shop_product import ShopProduct
from app.modules.gamification.models.shop_redemption import ShopRedemption

# Notifications
from app.modules.notifications.models.notification import Notification, NotificationReadState

__all__ = [
    "Character",
    "CoinTransaction",
    "Correction",
    "DailyCheckin",
    "DailyStat",
    "DictionaryAudioCache",
    "EmailOTP",
    "GamificationSetting",
    "Message",
    "LearningSection",
    "Lesson",
    "LessonAttempt",
    "Notification",
    "NotificationReadState",
    "PaymentTransaction",
    "PaymentWebhookEvent",
    "Scenario",
    "Session",
    "SessionScore",
    "ShopProduct",
    "ShopRedemption",
    "Subscription",
    "Unit",
    "User",
    "UserLessonProgress",
    "UserUnitProgress",
]

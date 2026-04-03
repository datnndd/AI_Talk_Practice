"""
SQLAlchemy ORM models for AI Talk Practice.

Import order matters for Alembic autogenerate — Base must be imported before
any model so all table definitions are registered on the metadata.
"""

from app.models.user import User
from app.models.scenario import Scenario, ScenarioVariation
from app.models.session import Session
from app.models.message import Message
from app.models.correction import Correction
from app.models.message_score import MessageScore
from app.models.session_score import SessionScore

__all__ = [
    "User",
    "Scenario",
    "ScenarioVariation",
    "Session",
    "Message",
    "Correction",
    "MessageScore",
    "SessionScore",
]

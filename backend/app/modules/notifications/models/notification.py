from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.users.models.user import User


class Notification(Base, TimestampMixin):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sender_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    recipient_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    audience: Mapped[str] = mapped_column(String(20), nullable=False)
    title: Mapped[str] = mapped_column(String(120), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)

    sender: Mapped["User"] = relationship("User", foreign_keys=[sender_user_id])
    recipient: Mapped["User | None"] = relationship("User", foreign_keys=[recipient_user_id])

    __table_args__ = (
        Index("ix_notifications_recipient_created", "recipient_user_id", "created_at"),
    )


class NotificationReadState(Base):
    __tablename__ = "notification_reads"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    notification_id: Mapped[int] = mapped_column(ForeignKey("notifications.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    read_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    notification: Mapped["Notification"] = relationship("Notification")
    user: Mapped["User"] = relationship("User")

    __table_args__ = (
        UniqueConstraint("notification_id", "user_id"),
        Index("ix_notification_reads_user_notification", "user_id", "notification_id"),
    )

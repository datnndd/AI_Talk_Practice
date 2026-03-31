"""Correction model."""

from sqlalchemy import String, Text, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin


class Correction(Base, TimestampMixin):
    __tablename__ = "corrections"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[int] = mapped_column(Integer, ForeignKey("messages.id"), index=True)
    original_text: Mapped[str] = mapped_column(Text)
    corrected_text: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    error_type: Mapped[str] = mapped_column(String(30))  # grammar, vocabulary, naturalness

    # Relationships
    message = relationship("Message", back_populates="corrections")

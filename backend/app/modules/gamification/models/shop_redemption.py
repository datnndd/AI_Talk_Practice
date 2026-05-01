from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base_class import Base, TimestampMixin

if TYPE_CHECKING:
    from app.modules.gamification.models.shop_product import ShopProduct
    from app.modules.users.models.user import User


class ShopRedemption(Base, TimestampMixin):
    __tablename__ = "shop_redemptions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("shop_products.id"), nullable=False, index=True)
    product_name: Mapped[str] = mapped_column(String(160), nullable=False)
    price_coin: Mapped[int] = mapped_column(Integer, nullable=False)
    recipient_name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str] = mapped_column(String(40), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    note: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending", server_default="pending", index=True)
    refunded: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")

    product: Mapped["ShopProduct"] = relationship("ShopProduct", back_populates="redemptions")
    user: Mapped["User"] = relationship("User")

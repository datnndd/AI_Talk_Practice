from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.gamification.models.coin_transaction import CoinTransaction
from app.modules.gamification.schemas.admin_gamification import (
    AdminGamificationOverviewRead,
    AdminShopProductRead,
    AdminShopProductWrite,
    AdminShopRedemptionRead,
    AdminShopRedemptionStatusUpdate,
    GamificationSettingsRead,
    GamificationSettingsUpdateRequest,
)
from app.modules.gamification.models.daily_checkin import DailyCheckin
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.models.gamification_setting import GamificationSetting
from app.modules.gamification.models.shop_product import ShopProduct
from app.modules.gamification.models.shop_redemption import ShopRedemption
from app.modules.gamification.settings import get_effective_rules
from app.modules.sessions.models.session import Session
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User


def _settings_payload(settings: GamificationSettingsRead) -> dict[str, Any]:
    return settings.model_dump(mode="json")


class AdminGamificationService:
    @staticmethod
    async def list_shop_products(db: AsyncSession) -> list[AdminShopProductRead]:
        rows = (await db.execute(select(ShopProduct).order_by(ShopProduct.sort_order.asc(), ShopProduct.id.asc()))).scalars().all()
        return [AdminShopProductRead.model_validate(row, from_attributes=True) for row in rows]

    @staticmethod
    async def create_shop_product(db: AsyncSession, body: AdminShopProductWrite) -> AdminShopProductRead:
        existing = (await db.execute(select(ShopProduct).where(ShopProduct.code == body.code))).scalar_one_or_none()
        if existing is not None:
            raise BadRequestError("Shop product code already exists.")
        product = ShopProduct(**body.model_dump())
        db.add(product)
        await db.commit()
        await db.refresh(product)
        return AdminShopProductRead.model_validate(product, from_attributes=True)

    @staticmethod
    async def update_shop_product(db: AsyncSession, product_id: int, body: AdminShopProductWrite) -> AdminShopProductRead:
        product = await db.get(ShopProduct, product_id)
        if product is None:
            raise NotFoundError("Shop product not found.")
        existing = (await db.execute(select(ShopProduct).where(ShopProduct.code == body.code, ShopProduct.id != product_id))).scalar_one_or_none()
        if existing is not None:
            raise BadRequestError("Shop product code already exists.")
        for key, value in body.model_dump().items():
            setattr(product, key, value)
        await db.commit()
        await db.refresh(product)
        return AdminShopProductRead.model_validate(product, from_attributes=True)

    @staticmethod
    async def hide_shop_product(db: AsyncSession, product_id: int) -> AdminShopProductRead:
        product = await db.get(ShopProduct, product_id)
        if product is None:
            raise NotFoundError("Shop product not found.")
        product.is_active = False
        await db.commit()
        await db.refresh(product)
        return AdminShopProductRead.model_validate(product, from_attributes=True)

    @staticmethod
    def _serialize_redemption(redemption: ShopRedemption) -> AdminShopRedemptionRead:
        return AdminShopRedemptionRead(
            id=redemption.id,
            user_id=redemption.user_id,
            user_email=redemption.user.email,
            user_display_name=redemption.user.display_name,
            product_id=redemption.product_id,
            product_name=redemption.product_name,
            price_coin=redemption.price_coin,
            recipient_name=redemption.recipient_name,
            phone=redemption.phone,
            address=redemption.address,
            note=redemption.note,
            status=redemption.status,
            refunded=redemption.refunded,
            created_at=redemption.created_at,
            updated_at=redemption.updated_at,
        )

    @classmethod
    async def list_shop_redemptions(cls, db: AsyncSession) -> list[AdminShopRedemptionRead]:
        rows = (
            await db.execute(
                select(ShopRedemption)
                .options(selectinload(ShopRedemption.user))
                .order_by(ShopRedemption.created_at.desc(), ShopRedemption.id.desc())
            )
        ).scalars().all()
        return [cls._serialize_redemption(row) for row in rows]

    @classmethod
    async def update_shop_redemption_status(
        cls,
        db: AsyncSession,
        redemption_id: int,
        body: AdminShopRedemptionStatusUpdate,
    ) -> AdminShopRedemptionRead:
        redemption = await db.get(ShopRedemption, redemption_id)
        if redemption is None:
            raise NotFoundError("Shop redemption not found.")
        redemption.status = body.status
        if body.status == "cancelled" and not redemption.refunded:
            user = await db.get(User, redemption.user_id)
            user.coin_balance = (user.coin_balance or 0) + redemption.price_coin
            redemption.refunded = True
            db.add(
                CoinTransaction(
                    user_id=user.id,
                    type="refund_shop_redemption",
                    amount=redemption.price_coin,
                    balance_after=user.coin_balance,
                    reference_type="shop_redemption",
                    reference_id=str(redemption.id),
                    transaction_metadata={"status": "cancelled"},
                )
            )
        await db.commit()
        redemption = (
            await db.execute(
                select(ShopRedemption)
                .options(selectinload(ShopRedemption.user))
                .where(ShopRedemption.id == redemption_id)
            )
        ).scalar_one()
        return cls._serialize_redemption(redemption)

    @staticmethod
    async def get_settings(db: AsyncSession) -> GamificationSettingsRead:
        rules = await get_effective_rules(db)
        return GamificationSettingsRead(
            level_coin_rewards=rules.level_coin_rewards,
            daily_checkin_coin_rewards=rules.daily_checkin_coin_rewards,
        )

    @staticmethod
    async def _upsert_setting(
        db: AsyncSession,
        *,
        key: str,
        value: Any,
        actor_id: int,
        description: str,
    ) -> None:
        setting = (
            await db.execute(select(GamificationSetting).where(GamificationSetting.key == key))
        ).scalar_one_or_none()
        if setting is None:
            db.add(
                GamificationSetting(
                    key=key,
                    value=value,
                    description=description,
                    updated_by_user_id=actor_id,
                )
            )
            return
        setting.value = value
        setting.description = description
        setting.updated_by_user_id = actor_id

    @classmethod
    async def update_settings(
        cls,
        db: AsyncSession,
        *,
        actor: User,
        body: GamificationSettingsUpdateRequest,
    ) -> GamificationSettingsRead:
        before = await cls.get_settings(db)
        values = _settings_payload(before)

        if body.level_coin_rewards is not None:
            values["level_coin_rewards"] = body.level_coin_rewards
        if body.daily_checkin_coin_rewards is not None:
            values["daily_checkin_coin_rewards"] = body.daily_checkin_coin_rewards

        await cls._upsert_setting(
            db,
            key="level_coin_rewards",
            value=values["level_coin_rewards"],
            actor_id=actor.id,
            description="Coin rewards granted when users reach specific levels",
        )
        await cls._upsert_setting(
            db,
            key="daily_checkin_coin_rewards",
            value=values["daily_checkin_coin_rewards"],
            actor_id=actor.id,
            description="Tiered Coin rewards granted by daily check-in streak day",
        )
        await db.commit()
        return await cls.get_settings(db)

    @staticmethod
    async def get_overview(db: AsyncSession, target_date: date) -> AdminGamificationOverviewRead:
        start_at = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        end_at = start_at + timedelta(days=1)
        today_daily_user_ids = {
            row[0]
            for row in (
                await db.execute(
                    select(DailyStat.user_id).where(DailyStat.date == target_date, DailyStat.lessons_completed > 0)
                )
            ).all()
        }
        today_session_user_ids = {
            row[0]
            for row in (
                await db.execute(
                    select(Session.user_id).where(Session.started_at >= start_at, Session.started_at < end_at)
                )
            ).all()
        }
        active_today = today_daily_user_ids | today_session_user_ids

        checkins_today = int(
            (await db.execute(select(func.count(DailyCheckin.id)).where(DailyCheckin.date == target_date))).scalar_one()
            or 0
        )
        coins_in_circulation = int(
            (
                await db.execute(select(func.coalesce(func.sum(User.coin_balance), 0)).where(User.deleted_at.is_(None)))
            ).scalar_one()
            or 0
        )
        active_users = int(
            (await db.execute(select(func.count(User.id)).where(User.deleted_at.is_(None)))).scalar_one() or 0
        )
        active_pro_users = int(
            (
                await db.execute(
                    select(func.count(Subscription.id))
                    .join(User, User.id == Subscription.user_id)
                    .where(
                        User.deleted_at.is_(None),
                        Subscription.status == "active",
                        Subscription.tier.in_(["PRO", "ENTERPRISE"]),
                    )
                )
            ).scalar_one()
            or 0
        )
        pro_upgrade_rate = round(active_pro_users / active_users, 4) if active_users else 0.0

        return AdminGamificationOverviewRead(
            date=target_date,
            active_users_today=len(active_today),
            checkins_today=checkins_today,
            coins_in_circulation=coins_in_circulation,
            pro_upgrade_rate=pro_upgrade_rate,
        )

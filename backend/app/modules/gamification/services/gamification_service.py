from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.modules.curriculum.models import Unit
from app.modules.gamification.models.coin_transaction import CoinTransaction
from app.modules.gamification.models.shop_product import ShopProduct
from app.modules.gamification.models.shop_redemption import ShopRedemption
from app.modules.gamification.models.daily_checkin import DailyCheckin
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.schemas import (
    CheckInRead,
    CheckInResponse,
    CoinRead,
    GamificationDashboard,
    LeaderboardEntryRead,
    LeaderboardPeriod,
    LeaderboardRead,
    LessonCompleteResponse,
    RewardRead,
    ShopItemRead,
    ShopRedeemResponse,
    ShopRedemptionRead,
    ShopRead,
    XPRead,
)
from app.modules.gamification.settings import (
    GamificationRules,
    get_effective_rules,
    level_from_total_xp,
    level_progress_from_total_xp,
    tiered_coin_reward,
)
from app.modules.users.models.user import User


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _today() -> date:
    return _utcnow().date()


def _as_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value


class GamificationService:
    @classmethod
    async def get_leaderboard(
        cls,
        db: AsyncSession,
        user: User,
        *,
        period: LeaderboardPeriod = "weekly",
        limit: int = 5,
    ) -> LeaderboardRead:
        today = _today()

        week_start = today - timedelta(days=today.weekday())
        weekly_scores = (
            select(
                DailyStat.user_id.label("user_id"),
                func.coalesce(func.sum(DailyStat.xp_earned), 0).label("score"),
            )
            .where(DailyStat.date >= week_start, DailyStat.date <= today)
            .group_by(DailyStat.user_id)
            .subquery()
        )
        score_expr = func.coalesce(weekly_scores.c.score, 0)
        source_stmt = (
            select(
                User.id.label("user_id"),
                User.display_name.label("display_name"),
                User.email.label("email"),
                User.avatar.label("avatar"),
                score_expr.label("score"),
                func.row_number().over(order_by=(score_expr.desc(), User.id.asc())).label("rank"),
            )
            .select_from(User)
            .outerjoin(weekly_scores, weekly_scores.c.user_id == User.id)
            .where(User.deleted_at.is_(None))
        )

        ranked = source_stmt.subquery()
        top_rows = (
            await db.execute(select(ranked).where(ranked.c.rank <= limit).order_by(ranked.c.rank.asc()))
        ).mappings().all()
        current_row = (await db.execute(select(ranked).where(ranked.c.user_id == user.id))).mappings().one()

        return LeaderboardRead(
            period=period,
            entries=[cls._serialize_leaderboard_row(row) for row in top_rows],
            current_user=cls._serialize_leaderboard_row(current_row),
        )

    @classmethod
    async def get_dashboard(cls, db: AsyncSession, user: User) -> GamificationDashboard:
        await cls._ensure_user_state(user)
        rules = await get_effective_rules(db)
        dashboard = await cls._build_dashboard(db, user, rules)
        await db.commit()
        return dashboard

    @classmethod
    async def award_lesson_completion(
        cls,
        db: AsyncSession,
        *,
        user: User,
        lesson: Unit,
    ) -> LessonCompleteResponse:
        await cls._ensure_user_state(user)
        rules = await get_effective_rules(db)
        before_level = level_from_total_xp(user.total_xp or 0)
        today = _today()
        daily_stat = await cls._get_or_create_daily_stat(db, user.id, today)

        xp_earned = int(lesson.xp_reward or 0)
        lesson_coin_earned = int(lesson.coin_reward or 0)
        user.total_xp = (user.total_xp or 0) + xp_earned
        after_level = level_from_total_xp(user.total_xp or 0)
        level_coin_reward = cls._level_coin_reward(rules, before_level=before_level, after_level=after_level)
        coin_earned = lesson_coin_earned + level_coin_reward

        user.coin_balance = (user.coin_balance or 0) + coin_earned
        user.total_lessons_completed = (user.total_lessons_completed or 0) + 1
        daily_stat.xp_earned = (daily_stat.xp_earned or 0) + xp_earned
        daily_stat.lessons_completed = (daily_stat.lessons_completed or 0) + 1
        await cls._record_coin_transaction(
            db,
            user,
            amount=lesson_coin_earned,
            transaction_type="earn_lesson",
            reference_type="lesson",
            reference_id=str(lesson.id),
            metadata={"xp_earned": xp_earned},
        )
        await cls._record_coin_transaction(
            db,
            user,
            amount=level_coin_reward,
            transaction_type="earn_level_reward",
            reference_type="level",
            reference_id=str(after_level),
            metadata={"before_level": before_level, "after_level": after_level},
        )
        dashboard = await cls._build_dashboard(db, user, rules)
        return LessonCompleteResponse(
            reward=RewardRead(
                xp_earned=xp_earned,
                coin_earned=coin_earned,
                levels_gained=max(0, after_level - before_level),
                level_coin_reward=level_coin_reward,
            ),
            dashboard=dashboard,
        )

    @classmethod
    async def check_in(cls, db: AsyncSession, user: User, *, allow_existing: bool = False) -> CheckInResponse:
        await cls._ensure_user_state(user)
        rules = await get_effective_rules(db)
        today = _today()
        existing = (
            await db.execute(select(DailyCheckin).where(DailyCheckin.user_id == user.id, DailyCheckin.date == today))
        ).scalar_one_or_none()
        if existing is not None:
            if allow_existing:
                dashboard = await cls._build_dashboard(db, user, rules)
                await db.commit()
                return CheckInResponse(
                    date=today,
                    streak_day=existing.streak_day,
                    coin_earned=0,
                    dashboard=dashboard,
                    already_checked_in=True,
                )
            raise BadRequestError("You have already checked in today.")

        latest = await cls._latest_checkin(db, user.id)
        streak_day = (latest.streak_day + 1) if latest and latest.date == today - timedelta(days=1) else 1
        coin_earned = tiered_coin_reward(rules.daily_checkin_coin_rewards, streak_day)
        user.coin_balance = (user.coin_balance or 0) + coin_earned
        checkin = DailyCheckin(user_id=user.id, date=today, streak_day=streak_day, coin_earned=coin_earned)
        db.add(checkin)
        await cls._record_coin_transaction(
            db,
            user,
            amount=coin_earned,
            transaction_type="earn_daily_checkin",
            reference_type="daily_checkin",
            reference_id=str(today),
            metadata={"streak_day": streak_day},
        )
        dashboard = await cls._build_dashboard(db, user, rules)
        await db.commit()
        return CheckInResponse(
            date=today,
            streak_day=streak_day,
            coin_earned=coin_earned,
            dashboard=dashboard,
            already_checked_in=False,
        )

    @staticmethod
    async def get_shop(db: AsyncSession) -> ShopRead:
        rows = (
            await db.execute(
                select(ShopProduct)
                .where(ShopProduct.is_active.is_(True), ShopProduct.stock_quantity > 0)
                .order_by(ShopProduct.sort_order.asc(), ShopProduct.id.asc())
            )
        ).scalars().all()
        return ShopRead(items=[ShopItemRead.model_validate(item, from_attributes=True) for item in rows])

    @classmethod
    async def redeem_shop_product(cls, db: AsyncSession, user: User, body) -> ShopRedeemResponse:
        await cls._ensure_user_state(user)
        product = (
            await db.execute(select(ShopProduct).where(ShopProduct.code == body.product_code))
        ).scalar_one_or_none()
        if product is None or not product.is_active:
            raise BadRequestError("Shop item not found.")
        if product.stock_quantity <= 0:
            raise BadRequestError("Shop item is out of stock.")
        if user.coin_balance < product.price_coin:
            raise BadRequestError("Not enough Coin.")

        user.coin_balance -= product.price_coin
        product.stock_quantity -= 1
        redemption = ShopRedemption(
            user_id=user.id,
            product_id=product.id,
            product_name=product.name,
            price_coin=product.price_coin,
            recipient_name=body.recipient_name.strip(),
            phone=body.phone.strip(),
            address=body.address.strip(),
            note=body.note.strip() if body.note else None,
            status="pending",
        )
        db.add(redemption)
        await db.flush()
        await cls._record_coin_transaction(
            db,
            user,
            amount=-product.price_coin,
            transaction_type="spend_shop_redeem",
            reference_type="shop_redemption",
            reference_id=str(redemption.id),
            metadata={"product_id": product.id, "product_code": product.code},
        )
        rules = await get_effective_rules(db)
        dashboard = await cls._build_dashboard(db, user, rules)
        await db.commit()
        await db.refresh(redemption)
        await db.refresh(product)
        item = ShopItemRead.model_validate(product, from_attributes=True)
        return ShopRedeemResponse(
            item=item,
            redemption=ShopRedemptionRead.model_validate(redemption, from_attributes=True),
            coin_spent=product.price_coin,
            dashboard=dashboard,
        )

    @staticmethod
    async def _ensure_user_state(user: User) -> None:
        user.total_xp = user.total_xp or 0
        user.coin_balance = user.coin_balance or 0
        user.total_lessons_completed = user.total_lessons_completed or 0

    @staticmethod
    async def _get_or_create_daily_stat(db: AsyncSession, user_id: int, stat_date: date) -> DailyStat:
        result = await db.execute(
            select(DailyStat).where(DailyStat.user_id == user_id, DailyStat.date == stat_date)
        )
        daily_stat = result.scalar_one_or_none()
        if daily_stat is not None:
            return daily_stat
        daily_stat = DailyStat(user_id=user_id, date=stat_date)
        db.add(daily_stat)
        await db.flush()
        return daily_stat

    @staticmethod
    async def _latest_checkin(db: AsyncSession, user_id: int) -> DailyCheckin | None:
        return (
            await db.execute(
                select(DailyCheckin)
                .where(DailyCheckin.user_id == user_id)
                .order_by(DailyCheckin.date.desc(), DailyCheckin.id.desc())
                .limit(1)
            )
        ).scalar_one_or_none()

    @classmethod
    async def _build_dashboard(
        cls,
        db: AsyncSession,
        user: User,
        rules: GamificationRules,
    ) -> GamificationDashboard:
        today = _today()
        daily_stat = await cls._get_or_create_daily_stat(db, user.id, today)
        progress = level_progress_from_total_xp(user.total_xp or 0)
        check_in = await cls._checkin_read(db, user.id, rules)

        return GamificationDashboard(
            xp=XPRead(
                total=user.total_xp or 0,
                today=daily_stat.xp_earned or 0,
                level=progress.level,
                level_progress=progress.level_progress,
                level_size=progress.level_size,
                xp_to_next_level=progress.xp_to_next_level,
            ),
            coin=CoinRead(balance=user.coin_balance or 0),
            check_in=check_in,
        )

    @classmethod
    async def _checkin_read(cls, db: AsyncSession, user_id: int, rules: GamificationRules) -> CheckInRead:
        today = _today()
        latest = await cls._latest_checkin(db, user_id)
        if latest is None:
            return CheckInRead(
                checked_in_today=False,
                current_streak=0,
                today_coin_reward=tiered_coin_reward(rules.daily_checkin_coin_rewards, 1),
            )
        if latest.date == today:
            return CheckInRead(
                checked_in_today=True,
                current_streak=latest.streak_day,
                today_coin_reward=latest.coin_earned,
            )
        current_streak = latest.streak_day if latest.date == today - timedelta(days=1) else 0
        next_streak_day = current_streak + 1 if current_streak else 1
        return CheckInRead(
            checked_in_today=False,
            current_streak=current_streak,
            today_coin_reward=tiered_coin_reward(rules.daily_checkin_coin_rewards, next_streak_day),
        )

    @staticmethod
    def _level_coin_reward(rules: GamificationRules, *, before_level: int, after_level: int) -> int:
        if after_level <= before_level:
            return 0
        return sum(int(rules.level_coin_rewards.get(str(level), 0)) for level in range(before_level + 1, after_level + 1))

    @staticmethod
    async def _record_coin_transaction(
        db: AsyncSession,
        user: User,
        *,
        amount: int,
        transaction_type: str,
        reference_type: str | None = None,
        reference_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        if amount == 0:
            return
        db.add(
            CoinTransaction(
                user_id=user.id,
                type=transaction_type,
                amount=amount,
                balance_after=user.coin_balance,
                reference_type=reference_type,
                reference_id=reference_id,
                transaction_metadata=metadata,
            )
        )


    @staticmethod
    def _serialize_leaderboard_row(row: dict) -> LeaderboardEntryRead:
        return LeaderboardEntryRead(
            user_id=int(row["user_id"]),
            rank=int(row["rank"]),
            score=int(row["score"] or 0),
            display_name=row["display_name"],
            email=row["email"],
            avatar=row["avatar"],
        )



from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError
from app.modules.curriculum.models import Lesson
from app.modules.gamification.models.coin_transaction import CoinTransaction
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
    ShopPurchaseResponse,
    ShopRead,
    XPRead,
)
from app.modules.gamification.settings import (
    SHOP_ITEMS,
    GamificationRules,
    get_effective_rules,
    level_from_total_xp,
    level_progress_from_total_xp,
    tiered_coin_reward,
)
from app.modules.users.models.subscription import Subscription
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

        if period == "weekly":
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
                    User.target_language.label("target_language"),
                    score_expr.label("score"),
                    func.row_number().over(order_by=(score_expr.desc(), User.id.asc())).label("rank"),
                )
                .select_from(User)
                .outerjoin(weekly_scores, weekly_scores.c.user_id == User.id)
                .where(User.deleted_at.is_(None))
            )
        else:
            score_expr = func.coalesce(User.total_xp, 0)
            source_stmt = (
                select(
                    User.id.label("user_id"),
                    User.display_name.label("display_name"),
                    User.email.label("email"),
                    User.avatar.label("avatar"),
                    User.target_language.label("target_language"),
                    score_expr.label("score"),
                    func.row_number().over(order_by=(score_expr.desc(), User.id.asc())).label("rank"),
                )
                .select_from(User)
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
        lesson: Lesson,
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
    async def check_in(cls, db: AsyncSession, user: User) -> CheckInResponse:
        await cls._ensure_user_state(user)
        rules = await get_effective_rules(db)
        today = _today()
        existing = (
            await db.execute(select(DailyCheckin).where(DailyCheckin.user_id == user.id, DailyCheckin.date == today))
        ).scalar_one_or_none()
        if existing is not None:
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
        return CheckInResponse(date=today, streak_day=streak_day, coin_earned=coin_earned, dashboard=dashboard)

    @staticmethod
    def get_shop() -> ShopRead:
        return ShopRead(items=[ShopItemRead(**item) for item in SHOP_ITEMS.values()])

    @classmethod
    async def purchase_shop_item(cls, db: AsyncSession, user: User, item_code: str) -> ShopPurchaseResponse:
        await cls._ensure_user_state(user)
        item_payload = SHOP_ITEMS.get(item_code)
        if item_payload is None:
            raise BadRequestError("Shop item not found.")
        item = ShopItemRead(**item_payload)
        if user.coin_balance < item.price_coin:
            raise BadRequestError("Not enough Coin.")

        user.coin_balance -= item.price_coin
        expires_at = await cls._activate_subscription_ticket(db, user, duration_days=item.duration_days or 1)
        await cls._record_coin_transaction(
            db,
            user,
            amount=-item.price_coin,
            transaction_type="spend_shop_purchase",
            reference_type="shop_item",
            reference_id=item.code,
            metadata={"item_type": item.type, "duration_days": item.duration_days},
        )
        rules = await get_effective_rules(db)
        dashboard = await cls._build_dashboard(db, user, rules)
        await db.commit()
        return ShopPurchaseResponse(
            item=item,
            coin_spent=item.price_coin,
            subscription_expires_at=expires_at,
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
    async def _activate_subscription_ticket(db: AsyncSession, user: User, *, duration_days: int) -> datetime:
        subscription = user.subscription
        if subscription is None:
            subscription = Subscription(user_id=user.id)
            db.add(subscription)
            user.subscription = subscription

        now = _utcnow()
        current_expiry = subscription.expires_at
        if current_expiry is not None:
            current_expiry = _as_aware(current_expiry)
        base = current_expiry if current_expiry and current_expiry > now else now
        expires_at = base + timedelta(days=duration_days)
        subscription.tier = "PRO"
        subscription.status = "active"
        subscription.expires_at = expires_at
        features = dict(subscription.features or {})
        features.update({"live_ai_practice": True, "advanced_scenarios": True, "premium_tutor": True})
        subscription.features = features
        return expires_at

    @staticmethod
    def _serialize_leaderboard_row(row: dict) -> LeaderboardEntryRead:
        return LeaderboardEntryRead(
            user_id=int(row["user_id"]),
            rank=int(row["rank"]),
            score=int(row["score"] or 0),
            display_name=row["display_name"],
            email=row["email"],
            avatar=row["avatar"],
            target_language=row["target_language"],
        )

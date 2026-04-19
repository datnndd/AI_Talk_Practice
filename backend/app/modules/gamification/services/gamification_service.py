from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.gamification.models.achievement import Achievement
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.models.gem_transaction import GemTransaction
from app.modules.gamification.models.user_achievement import UserAchievement
from app.modules.gamification.schemas import (
    AchievementRead,
    GamificationDashboard,
    GemRead,
    HeartRead,
    LessonCompleteRequest,
    LessonCompleteResponse,
    RewardRead,
    StreakRead,
    UnlockedAchievementRead,
    XPRead,
)
from app.modules.gamification.settings import (
    DEFAULT_HEART_PURCHASE_PRICES,
    DEFAULT_XP_BY_LESSON_TYPE,
    SPEAKING_LESSON_TYPES,
    XP_PER_LEVEL,
    GamificationRules,
    get_effective_rules,
)
from app.modules.users.models.user import User

XP_BY_LESSON_TYPE = DEFAULT_XP_BY_LESSON_TYPE
HEART_PURCHASE_PRICES = {int(key): value for key, value in DEFAULT_HEART_PURCHASE_PRICES.items()}

ACHIEVEMENT_CATALOG = [
    {
        "code": "first_lesson",
        "name": "Bai hoc dau tien",
        "description": "Hoan thanh 1 bai hoc.",
        "gem_reward": 20,
        "icon_url": "badge-first-lesson",
        "condition": {"total_lessons_completed": 1},
    },
    {
        "code": "streak_3",
        "name": "Bat dau nong may",
        "description": "Dat streak 3 ngay.",
        "gem_reward": 30,
        "icon_url": "badge-streak-3",
        "condition": {"current_streak": 3},
    },
    {
        "code": "streak_7",
        "name": "Mot tuan ben bi",
        "description": "Dat streak 7 ngay.",
        "gem_reward": 50,
        "icon_url": "badge-streak-7",
        "condition": {"current_streak": 7},
    },
    {
        "code": "streak_30",
        "name": "Thoi quen that su",
        "description": "Dat streak 30 ngay.",
        "gem_reward": 200,
        "icon_url": "badge-streak-30",
        "condition": {"current_streak": 30},
    },
    {
        "code": "xp_1000",
        "name": "Level dau tien",
        "description": "Dat 1000 XP.",
        "gem_reward": 100,
        "icon_url": "badge-xp-1000",
        "condition": {"total_xp": 1000},
    },
    {
        "code": "speaking_10",
        "name": "Dam noi roi",
        "description": "Hoan thanh 10 bai luyen noi.",
        "gem_reward": 80,
        "icon_url": "badge-speaking-10",
        "condition": {"total_speaking_lessons_completed": 10},
    },
    {
        "code": "speaking_50",
        "name": "Noi tu tin hon",
        "description": "Hoan thanh 50 bai luyen noi.",
        "gem_reward": 250,
        "icon_url": "badge-speaking-50",
        "condition": {"total_speaking_lessons_completed": 50},
    },
    {
        "code": "daily_goal_7",
        "name": "Giu nhip hoc",
        "description": "Dat Daily XP Goal 7 ngay.",
        "gem_reward": 100,
        "icon_url": "badge-daily-goal-7",
        "condition": {"daily_goal_streak": 7},
    },
    {
        "code": "perfect_score_5",
        "name": "Phong do tot",
        "description": "Dat diem cao trong 5 bai.",
        "gem_reward": 100,
        "icon_url": "badge-perfect-5",
        "condition": {"perfect_score_count": 5},
    },
    {
        "code": "vocab_100",
        "name": "Tu vung nen tang",
        "description": "Hoan thanh 100 muc tu vung.",
        "gem_reward": 150,
        "icon_url": "badge-vocab-100",
        "condition": {"total_vocabulary_lessons_completed": 100},
    },
]


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
    async def get_dashboard(cls, db: AsyncSession, user: User) -> GamificationDashboard:
        await cls._ensure_catalog(db)
        await cls._ensure_user_state(user)
        await cls._reset_expired_streak(user)
        rules = await get_effective_rules(db)
        await cls._refill_hearts(user, rules)
        dashboard = await cls._build_dashboard(db, user, rules)
        await db.commit()
        return dashboard

    @classmethod
    async def update_daily_goal(cls, db: AsyncSession, user: User, daily_xp_goal: int) -> GamificationDashboard:
        await cls._ensure_user_state(user)
        user.daily_xp_goal = daily_xp_goal
        rules = await get_effective_rules(db)
        dashboard = await cls._build_dashboard(db, user, rules)
        await db.commit()
        return dashboard

    @classmethod
    async def complete_lesson(
        cls,
        db: AsyncSession,
        user: User,
        body: LessonCompleteRequest,
    ) -> LessonCompleteResponse:
        await cls._ensure_catalog(db)
        await cls._ensure_user_state(user)
        rules = await get_effective_rules(db)
        today = _today()
        daily_stat = await cls._get_or_create_daily_stat(db, user.id, today)

        xp_earned = rules.xp_by_lesson_type[body.lesson_type]
        gem_earned = xp_earned // rules.xp_per_gem

        user.total_xp += xp_earned
        user.gem_balance += gem_earned
        user.total_lessons_completed += 1
        if body.lesson_type in SPEAKING_LESSON_TYPES:
            user.total_speaking_lessons_completed += 1
            daily_stat.speaking_lessons_completed += 1
        if body.lesson_type == "vocabulary":
            user.total_vocabulary_lessons_completed += 1
            daily_stat.vocabulary_lessons_completed += 1
        if body.score is not None and body.score >= 90:
            user.perfect_score_count += 1

        daily_stat.xp_earned += xp_earned
        daily_stat.lessons_completed += 1

        cls._update_streak_for_completed_lesson(user, today)
        cls._update_daily_goal_streak(user, daily_stat, today)
        await cls._record_gem_transaction(
            db,
            user,
            amount=gem_earned,
            transaction_type="earn_lesson",
            reference_type="lesson_type",
            reference_id=body.lesson_type,
            metadata={"xp_earned": xp_earned},
        )

        unlocked = await cls._unlock_earned_achievements(db, user)
        dashboard = await cls._build_dashboard(db, user, rules)
        await db.commit()
        return LessonCompleteResponse(
            reward=RewardRead(xp_earned=xp_earned, gem_earned=gem_earned),
            unlocked_achievements=unlocked,
            dashboard=dashboard,
        )

    @classmethod
    async def purchase_hearts(cls, db: AsyncSession, user: User, hearts: int) -> tuple[int, int, GamificationDashboard]:
        await cls._ensure_user_state(user)
        if cls._has_unlimited_hearts(user):
            raise BadRequestError("Pro users already have unlimited Hearts.")

        rules = await get_effective_rules(db)
        await cls._refill_hearts(user, rules)
        price = rules.heart_purchase_prices[str(hearts)]
        if user.gem_balance < price:
            raise BadRequestError("Not enough Gem to buy Heart.")

        user.gem_balance -= price
        user.heart_balance = min(user.heart_max, user.heart_balance + hearts)
        if user.heart_balance >= user.heart_max:
            user.last_heart_refill_at = _utcnow()
        await cls._record_gem_transaction(
            db,
            user,
            amount=-price,
            transaction_type="spend_buy_heart",
            reference_type="heart_pack",
            reference_id=str(hearts),
            metadata={"hearts": hearts},
        )
        dashboard = await cls._build_dashboard(db, user, rules)
        await db.commit()
        return hearts, price, dashboard

    @classmethod
    async def consume_speaking_heart(cls, db: AsyncSession, user_id: int) -> None:
        result = await db.execute(
            select(User)
            .options(selectinload(User.subscription))
            .where(User.id == user_id, User.deleted_at.is_(None))
        )
        user = result.scalar_one_or_none()
        if user is None:
            raise NotFoundError("User not found")
        await cls._ensure_user_state(user)
        if cls._has_unlimited_hearts(user):
            return

        rules = await get_effective_rules(db)
        await cls._refill_hearts(user, rules)
        if user.heart_balance <= 0:
            raise BadRequestError("You are out of Heart. Wait for refill or buy more with Gem.")
        user.heart_balance -= 1
        user.last_heart_refill_at = _utcnow()
        await db.flush()

    @classmethod
    async def _ensure_catalog(cls, db: AsyncSession) -> None:
        result = await db.execute(select(Achievement))
        existing_by_code = {item.code: item for item in result.scalars().all()}
        changed = False
        for item in ACHIEVEMENT_CATALOG:
            existing = existing_by_code.get(item["code"])
            if existing is None:
                db.add(Achievement(**item))
                changed = True
                continue
            for field in ("name", "description", "icon_url", "gem_reward", "condition"):
                if getattr(existing, field) != item[field]:
                    setattr(existing, field, item[field])
                    changed = True
        if changed:
            await db.flush()

    @staticmethod
    async def _ensure_user_state(user: User) -> None:
        user.current_streak = user.current_streak or 0
        user.longest_streak = user.longest_streak or 0
        user.total_xp = user.total_xp or 0
        user.daily_xp_goal = user.daily_xp_goal or 50
        user.gem_balance = user.gem_balance or 0
        user.heart_max = user.heart_max or 5
        if user.heart_balance is None:
            user.heart_balance = user.heart_max
        user.total_lessons_completed = user.total_lessons_completed or 0
        user.total_speaking_lessons_completed = user.total_speaking_lessons_completed or 0
        user.total_vocabulary_lessons_completed = user.total_vocabulary_lessons_completed or 0
        user.perfect_score_count = user.perfect_score_count or 0
        user.daily_goal_streak = user.daily_goal_streak or 0
        if user.last_heart_refill_at is None:
            user.last_heart_refill_at = _utcnow()

    @staticmethod
    async def _reset_expired_streak(user: User) -> None:
        today = _today()
        if user.last_completed_lesson_date and user.last_completed_lesson_date < today - timedelta(days=1):
            user.current_streak = 0

    @classmethod
    async def _refill_hearts(cls, user: User, rules: GamificationRules) -> None:
        if cls._has_unlimited_hearts(user):
            return
        now = _utcnow()
        if user.heart_balance >= user.heart_max:
            return
        last_refill = _as_aware(user.last_heart_refill_at or now)
        elapsed_refills = int((now - last_refill).total_seconds() // (rules.heart_refill_minutes * 60))
        if elapsed_refills <= 0:
            return
        user.heart_balance = min(user.heart_max, user.heart_balance + elapsed_refills)
        user.last_heart_refill_at = last_refill + timedelta(minutes=rules.heart_refill_minutes * elapsed_refills)
        if user.heart_balance >= user.heart_max:
            user.last_heart_refill_at = now

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
    def _update_streak_for_completed_lesson(user: User, today: date) -> None:
        last_completed = user.last_completed_lesson_date
        if last_completed == today:
            return
        if last_completed == today - timedelta(days=1):
            user.current_streak += 1
        else:
            user.current_streak = 1
        user.longest_streak = max(user.longest_streak, user.current_streak)
        user.last_completed_lesson_date = today

    @staticmethod
    def _update_daily_goal_streak(user: User, daily_stat: DailyStat, today: date) -> None:
        if daily_stat.daily_goal_met or daily_stat.xp_earned < user.daily_xp_goal:
            return
        last_goal_date = user.last_daily_goal_date
        if last_goal_date == today:
            daily_stat.daily_goal_met = True
            return
        if last_goal_date == today - timedelta(days=1):
            user.daily_goal_streak += 1
        else:
            user.daily_goal_streak = 1
        user.last_daily_goal_date = today
        daily_stat.daily_goal_met = True

    @staticmethod
    async def _record_gem_transaction(
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
            GemTransaction(
                user_id=user.id,
                type=transaction_type,
                amount=amount,
                balance_after=user.gem_balance,
                reference_type=reference_type,
                reference_id=reference_id,
                transaction_metadata=metadata,
            )
        )

    @classmethod
    async def _unlock_earned_achievements(cls, db: AsyncSession, user: User) -> list[UnlockedAchievementRead]:
        achievements = (
            await db.execute(
                select(Achievement)
                .where(Achievement.is_active.is_(True), Achievement.deleted_at.is_(None))
                .order_by(Achievement.id)
            )
        ).scalars().all()
        existing_ids = {
            item.achievement_id
            for item in (
                await db.execute(select(UserAchievement).where(UserAchievement.user_id == user.id))
            ).scalars().all()
        }

        unlocked: list[UnlockedAchievementRead] = []
        now = _utcnow()
        for achievement in achievements:
            if achievement.id in existing_ids or not cls._achievement_condition_met(user, achievement.condition or {}):
                continue
            user_achievement = UserAchievement(user_id=user.id, achievement_id=achievement.id, unlocked_at=now)
            db.add(user_achievement)
            user.gem_balance += achievement.gem_reward
            await cls._record_gem_transaction(
                db,
                user,
                amount=achievement.gem_reward,
                transaction_type="earn_achievement",
                reference_type="achievement",
                reference_id=achievement.code,
                metadata={"achievement_id": achievement.id},
            )
            unlocked.append(cls._serialize_unlocked_achievement(achievement, now))
        if unlocked:
            await db.flush()
        return unlocked

    @staticmethod
    def _achievement_condition_met(user: User, condition: dict) -> bool:
        for field, expected in condition.items():
            if getattr(user, field, 0) < expected:
                return False
        return True

    @classmethod
    async def _build_dashboard(cls, db: AsyncSession, user: User, rules: GamificationRules) -> GamificationDashboard:
        today = _today()
        daily_stat = await cls._get_or_create_daily_stat(db, user.id, today)
        achievements = (
            await db.execute(
                select(Achievement)
                .where(Achievement.is_active.is_(True), Achievement.deleted_at.is_(None))
                .order_by(Achievement.id)
            )
        ).scalars().all()
        user_achievements = (
            await db.execute(
                select(UserAchievement, Achievement)
                .join(Achievement, Achievement.id == UserAchievement.achievement_id)
                .where(UserAchievement.user_id == user.id)
                .order_by(UserAchievement.unlocked_at.desc(), UserAchievement.id.desc())
            )
        ).all()

        level = (user.total_xp // XP_PER_LEVEL) + 1
        level_progress = user.total_xp % XP_PER_LEVEL
        next_refill_at = cls._next_heart_refill_at(user, rules)

        return GamificationDashboard(
            streak=StreakRead(
                current=user.current_streak,
                longest=user.longest_streak,
                last_completed_lesson_date=user.last_completed_lesson_date,
            ),
            xp=XPRead(
                total=user.total_xp,
                today=daily_stat.xp_earned,
                daily_goal=user.daily_xp_goal,
                level=level,
                level_progress=level_progress,
                daily_goal_met=daily_stat.xp_earned >= user.daily_xp_goal,
            ),
            gem=GemRead(balance=user.gem_balance),
            heart=HeartRead(
                current=None if cls._has_unlimited_hearts(user) else user.heart_balance,
                max=user.heart_max,
                is_unlimited=cls._has_unlimited_hearts(user),
                next_refill_at=next_refill_at,
            ),
            achievements={
                "available": [cls._serialize_achievement(item) for item in achievements],
                "unlocked": [
                    cls._serialize_unlocked_achievement(achievement, user_achievement.unlocked_at)
                    for user_achievement, achievement in user_achievements
                ],
            },
        )

    @staticmethod
    def _has_unlimited_hearts(user: User) -> bool:
        subscription = getattr(user, "subscription", None)
        return bool(subscription and subscription.tier in {"PRO", "ENTERPRISE"} and subscription.status == "active")

    @classmethod
    def _next_heart_refill_at(cls, user: User, rules: GamificationRules) -> datetime | None:
        if cls._has_unlimited_hearts(user) or user.heart_balance >= user.heart_max:
            return None
        return _as_aware(user.last_heart_refill_at or _utcnow()) + timedelta(minutes=rules.heart_refill_minutes)

    @staticmethod
    def _serialize_achievement(achievement: Achievement) -> AchievementRead:
        return AchievementRead(
            code=achievement.code,
            name=achievement.name,
            description=achievement.description,
            gem_reward=achievement.gem_reward,
            icon=achievement.icon_url,
        )

    @classmethod
    def _serialize_unlocked_achievement(
        cls,
        achievement: Achievement,
        unlocked_at: datetime,
    ) -> UnlockedAchievementRead:
        serialized = cls._serialize_achievement(achievement)
        return UnlockedAchievementRead(**serialized.model_dump(), unlocked_at=unlocked_at)

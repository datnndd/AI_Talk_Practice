from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.admin.services.audit_log_service import AdminAuditLogService
from app.modules.gamification.schemas.admin_gamification import (
    AchievementAdminRead,
    AchievementCreateRequest,
    AchievementUpdateRequest,
    AdminGamificationOverviewRead,
    GamificationSettingsRead,
    GamificationSettingsUpdateRequest,
)
from app.modules.gamification.models.achievement import Achievement
from app.modules.gamification.models.daily_stat import DailyStat
from app.modules.gamification.models.gamification_setting import GamificationSetting
from app.modules.gamification.settings import get_effective_rules
from app.modules.sessions.models.session import Session
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User


def _serialize_achievement_admin(achievement: Achievement) -> AchievementAdminRead:
    return AchievementAdminRead(
        id=achievement.id,
        code=achievement.code,
        name=achievement.name,
        description=achievement.description,
        icon=achievement.icon_url,
        gem_reward=achievement.gem_reward,
        condition=achievement.condition or {},
        is_active=achievement.is_active,
        deleted_at=achievement.deleted_at,
    )


def _settings_payload(settings: GamificationSettingsRead) -> dict[str, Any]:
    return settings.model_dump(mode="json")


class AdminGamificationService:
    @staticmethod
    async def get_settings(db: AsyncSession) -> GamificationSettingsRead:
        rules = await get_effective_rules(db)
        return GamificationSettingsRead(
            xp_by_lesson_type=rules.xp_by_lesson_type,
            xp_per_gem=rules.xp_per_gem,
            heart_purchase_prices=rules.heart_purchase_prices,
            heart_refill_minutes=rules.heart_refill_minutes,
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

        if body.xp_by_lesson_type is not None:
            values["xp_by_lesson_type"] = {**values["xp_by_lesson_type"], **body.xp_by_lesson_type}
        if body.xp_per_gem is not None:
            values["xp_per_gem"] = body.xp_per_gem
        if body.heart_purchase_prices is not None:
            values["heart_purchase_prices"] = {**values["heart_purchase_prices"], **body.heart_purchase_prices}
        if body.heart_refill_minutes is not None:
            values["heart_refill_minutes"] = body.heart_refill_minutes

        await cls._upsert_setting(
            db,
            key="xp_by_lesson_type",
            value=values["xp_by_lesson_type"],
            actor_id=actor.id,
            description="XP awarded by lesson type",
        )
        await cls._upsert_setting(
            db,
            key="xp_per_gem",
            value=values["xp_per_gem"],
            actor_id=actor.id,
            description="How much XP converts into one Gem",
        )
        await cls._upsert_setting(
            db,
            key="heart_purchase_prices",
            value=values["heart_purchase_prices"],
            actor_id=actor.id,
            description="Gem prices for Heart packs",
        )
        await cls._upsert_setting(
            db,
            key="heart_refill_minutes",
            value=values["heart_refill_minutes"],
            actor_id=actor.id,
            description="Minutes required to refill one Heart",
        )
        AdminAuditLogService.record(
            db,
            actor_user_id=actor.id,
            action="gamification.settings_updated",
            entity_type="gamification_settings",
            before=_settings_payload(before),
            after=values,
            reason=body.reason,
        )
        await db.commit()
        return await cls.get_settings(db)

    @staticmethod
    async def list_achievements(db: AsyncSession) -> list[AchievementAdminRead]:
        achievements = (
            await db.execute(select(Achievement).order_by(Achievement.deleted_at.is_not(None), Achievement.id))
        ).scalars().all()
        return [_serialize_achievement_admin(achievement) for achievement in achievements]

    @staticmethod
    async def get_achievement(db: AsyncSession, achievement_id: int) -> Achievement:
        achievement = await db.get(Achievement, achievement_id)
        if achievement is None:
            raise NotFoundError("Achievement not found")
        return achievement

    @classmethod
    async def create_achievement(
        cls,
        db: AsyncSession,
        *,
        actor: User,
        body: AchievementCreateRequest,
    ) -> AchievementAdminRead:
        achievement = Achievement(
            code=body.code,
            name=body.name,
            description=body.description,
            icon_url=body.icon,
            gem_reward=body.gem_reward,
            condition=body.condition,
            is_active=body.is_active,
        )
        db.add(achievement)
        try:
            await db.flush()
        except IntegrityError as exc:
            await db.rollback()
            raise BadRequestError("Achievement code already exists") from exc

        serialized = _serialize_achievement_admin(achievement)
        AdminAuditLogService.record(
            db,
            actor_user_id=actor.id,
            action="achievement.created",
            entity_type="achievement",
            entity_id=achievement.id,
            after=serialized.model_dump(mode="json"),
        )
        await db.commit()
        await db.refresh(achievement)
        return _serialize_achievement_admin(achievement)

    @classmethod
    async def update_achievement(
        cls,
        db: AsyncSession,
        *,
        actor: User,
        achievement_id: int,
        body: AchievementUpdateRequest,
    ) -> AchievementAdminRead:
        achievement = await cls.get_achievement(db, achievement_id)
        before = _serialize_achievement_admin(achievement).model_dump(mode="json")

        update_data = body.model_dump(exclude_unset=True)
        if "icon" in update_data:
            achievement.icon_url = update_data.pop("icon")
        for field, value in update_data.items():
            setattr(achievement, field, value)

        after = _serialize_achievement_admin(achievement).model_dump(mode="json")
        AdminAuditLogService.record(
            db,
            actor_user_id=actor.id,
            action="achievement.updated",
            entity_type="achievement",
            entity_id=achievement.id,
            before=before,
            after=after,
        )
        await db.commit()
        await db.refresh(achievement)
        return _serialize_achievement_admin(achievement)

    @classmethod
    async def delete_achievement(
        cls,
        db: AsyncSession,
        *,
        actor: User,
        achievement_id: int,
    ) -> AchievementAdminRead:
        achievement = await cls.get_achievement(db, achievement_id)
        before = _serialize_achievement_admin(achievement).model_dump(mode="json")
        achievement.is_active = False
        achievement.deleted_at = datetime.now(timezone.utc)
        after = _serialize_achievement_admin(achievement).model_dump(mode="json")
        AdminAuditLogService.record(
            db,
            actor_user_id=actor.id,
            action="achievement.deleted",
            entity_type="achievement",
            entity_id=achievement.id,
            before=before,
            after=after,
        )
        await db.commit()
        await db.refresh(achievement)
        return _serialize_achievement_admin(achievement)

    @staticmethod
    async def get_overview(db: AsyncSession, target_date: date) -> AdminGamificationOverviewRead:
        start_at = datetime.combine(target_date, time.min, tzinfo=timezone.utc)
        end_at = start_at + timedelta(days=1)
        previous_date = target_date - timedelta(days=1)

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

        previous_user_ids = {
            row[0]
            for row in (
                await db.execute(
                    select(DailyStat.user_id).where(DailyStat.date == previous_date, DailyStat.lessons_completed > 0)
                )
            ).all()
        }
        retained = active_today & previous_user_ids
        streak_retention_rate = round(len(retained) / len(previous_user_ids), 4) if previous_user_ids else 0.0

        speaking_sessions_started = int(
            (
                await db.execute(
                    select(func.count(Session.id)).where(Session.started_at >= start_at, Session.started_at < end_at)
                )
            ).scalar_one()
            or 0
        )
        gems_in_circulation = int(
            (
                await db.execute(select(func.coalesce(func.sum(User.gem_balance), 0)).where(User.deleted_at.is_(None)))
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
            streak_retention_rate=streak_retention_rate,
            speaking_sessions_started=speaking_sessions_started,
            gems_in_circulation=gems_in_circulation,
            pro_upgrade_rate=pro_upgrade_rate,
        )

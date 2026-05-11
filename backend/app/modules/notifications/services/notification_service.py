from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.modules.notifications.models.notification import Notification, NotificationReadState
from app.modules.notifications.schemas.notification import AdminNotificationCreateRequest, NotificationRead
from app.modules.users.models.subscription import Subscription
from app.modules.users.models.user import User


def _format_date(value: datetime | None) -> str:
    if value is None:
        return "soon"
    normalized = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return normalized.astimezone(timezone.utc).strftime("%Y-%m-%d")


def _serialize_notification(notification: Notification, read_at: datetime | None = None) -> NotificationRead:
    return NotificationRead(
        id=notification.id,
        audience=notification.audience,
        recipient_user_id=notification.recipient_user_id,
        title=notification.title,
        body=notification.body,
        created_at=notification.created_at,
        read_at=read_at,
    )


class NotificationService:
    @staticmethod
    async def _find_duplicate(
        db: AsyncSession,
        *,
        user_id: int,
        title: str,
        body: str,
    ) -> Notification | None:
        return (
            await db.execute(
                select(Notification)
                .where(
                    Notification.recipient_user_id == user_id,
                    Notification.title == title,
                    Notification.body == body,
                )
                .limit(1)
            )
        ).scalars().first()

    @classmethod
    async def create_system_notification(
        cls,
        db: AsyncSession,
        *,
        user_id: int,
        title: str,
        body: str,
    ) -> NotificationRead | None:
        if await cls._find_duplicate(db, user_id=user_id, title=title, body=body):
            return None

        notification = Notification(
            sender_user_id=None,
            recipient_user_id=user_id,
            audience="users",
            title=title,
            body=body,
        )
        db.add(notification)
        await db.flush()
        return _serialize_notification(notification)

    @classmethod
    async def ensure_vip_expiry_notifications(cls, db: AsyncSession, *, user: User) -> None:
        subscription = getattr(user, "subscription", None)
        if subscription is None:
            subscription = (
                await db.execute(select(Subscription).where(Subscription.user_id == user.id))
            ).scalar_one_or_none()
        if subscription is None or str(subscription.tier or "").upper() != "PRO":
            return
        if str(subscription.status or "").lower() != "active" or subscription.expires_at is None:
            return

        now = datetime.now(timezone.utc)
        expires_at = subscription.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if expires_at <= now:
            await cls.create_system_notification(
                db,
                user_id=user.id,
                title="VIP expired",
                body="Your Pro subscription has expired. Renew to keep Pro access.",
            )
            await db.commit()
            return

        days_left = (expires_at - now).total_seconds() / 86400
        if 0 < days_left <= 3:
            await cls.create_system_notification(
                db,
                user_id=user.id,
                title="VIP expiring soon",
                body=f"Your Pro subscription will expire on {_format_date(expires_at)}.",
            )
            await db.commit()

    @staticmethod
    async def create_admin_notifications(
        db: AsyncSession,
        *,
        actor: User,
        body: AdminNotificationCreateRequest,
    ) -> list[NotificationRead]:
        notifications: list[Notification] = []
        if body.audience == "all":
            notifications.append(
                Notification(
                    sender_user_id=actor.id,
                    recipient_user_id=None,
                    audience="all",
                    title=body.title,
                    body=body.body,
                )
            )
        else:
            for user_id in sorted(set(body.recipient_user_ids or [])):
                notifications.append(
                    Notification(
                        sender_user_id=actor.id,
                        recipient_user_id=user_id,
                        audience="users",
                        title=body.title,
                        body=body.body,
                    )
                )

        db.add_all(notifications)
        await db.flush()
        await db.commit()
        for notification in notifications:
            await db.refresh(notification)
        return [_serialize_notification(notification) for notification in notifications]

    @staticmethod
    async def list_admin_notifications(
        db: AsyncSession,
        *,
        page: int,
        page_size: int,
    ) -> tuple[list[NotificationRead], int]:
        stmt = (
            select(Notification)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        notifications = list((await db.execute(stmt)).scalars().all())
        total = int((await db.execute(select(func.count(Notification.id)))).scalar_one() or 0)
        return [_serialize_notification(notification) for notification in notifications], total

    @staticmethod
    async def list_for_user(
        db: AsyncSession,
        *,
        user: User,
        page: int,
        page_size: int,
    ) -> tuple[list[NotificationRead], int]:
        await NotificationService.ensure_vip_expiry_notifications(db, user=user)
        visibility = or_(Notification.recipient_user_id.is_(None), Notification.recipient_user_id == user.id)
        stmt = (
            select(Notification, NotificationReadState.read_at)
            .outerjoin(
                NotificationReadState,
                (NotificationReadState.notification_id == Notification.id)
                & (NotificationReadState.user_id == user.id),
            )
            .where(visibility)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        count_stmt = select(func.count(Notification.id)).where(visibility)
        rows = (await db.execute(stmt)).all()
        total = int((await db.execute(count_stmt)).scalar_one() or 0)
        return [_serialize_notification(notification, read_at) for notification, read_at in rows], total

    @staticmethod
    async def mark_read(db: AsyncSession, *, user: User, notification_id: int) -> NotificationRead:
        notification = (
            await db.execute(
                select(Notification).where(
                    Notification.id == notification_id,
                    or_(Notification.recipient_user_id.is_(None), Notification.recipient_user_id == user.id),
                )
            )
        ).scalar_one_or_none()
        if notification is None:
            raise NotFoundError("Notification not found")

        read_state = (
            await db.execute(
                select(NotificationReadState).where(
                    NotificationReadState.notification_id == notification.id,
                    NotificationReadState.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if read_state is None:
            read_state = NotificationReadState(
                notification_id=notification.id,
                user_id=user.id,
                read_at=datetime.now(timezone.utc),
            )
            db.add(read_state)
            await db.flush()

        await db.commit()
        await db.refresh(notification)
        return _serialize_notification(notification, read_state.read_at)

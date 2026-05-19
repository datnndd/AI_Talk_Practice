from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.payments.models import PaymentTransaction, SubscriptionPlan
from app.modules.payments.schemas.admin_payment import AdminSubscriptionPlanUpdateRequest
from app.modules.payments.schemas.admin_payment import PaymentDashboardRead
from app.modules.payments.schemas.admin_payment import PaymentOverviewRead
from app.modules.payments.schemas.admin_payment import PaymentPlanRevenueRead
from app.modules.payments.schemas.admin_payment import PaymentStatsBucketRead
from app.modules.payments.schemas.admin_payment import PaymentStatsRead
from app.modules.payments.schemas.admin_payment import PaymentStatusBreakdownRead
from app.modules.payments.schemas.admin_payment import PaymentVolumeBucketRead
from app.modules.payments.serializers import serialize_admin_payment_transaction
from app.modules.payments.services.payment_service import PaymentService
from app.modules.users.models.user import User


class AdminPaymentService:
    @staticmethod
    def _normalize_code(code: str) -> str:
        return code.strip().upper()

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    @staticmethod
    def _start_of_day(value: datetime) -> datetime:
        return AdminPaymentService._as_utc(value).replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _start_of_month(value: datetime) -> datetime:
        value = AdminPaymentService._as_utc(value)
        return value.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _start_of_year(value: datetime) -> datetime:
        value = AdminPaymentService._as_utc(value)
        return value.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _add_months(value: datetime, months: int) -> datetime:
        month_index = value.month - 1 + months
        year = value.year + month_index // 12
        month = month_index % 12 + 1
        return value.replace(year=year, month=month)

    @classmethod
    def _build_stat_buckets(cls, period: str) -> list[tuple[str, datetime]]:
        now = datetime.now(timezone.utc)
        if period == "day":
            today = cls._start_of_day(now)
            return [(day.strftime("%d/%m"), day) for day in (today - timedelta(days=offset) for offset in range(29, -1, -1))]
        if period == "month":
            current_month = cls._start_of_month(now)
            return [(month.strftime("%m/%Y"), month) for month in (cls._add_months(current_month, -offset) for offset in range(11, -1, -1))]
        current_year = cls._start_of_year(now)
        return [(str(year.year), year) for year in (current_year.replace(year=current_year.year - offset) for offset in range(4, -1, -1))]

    @classmethod
    def _bucket_key(cls, value: datetime, period: str) -> datetime:
        if period == "day":
            return cls._start_of_day(value)
        if period == "month":
            return cls._start_of_month(value)
        return cls._start_of_year(value)

    @classmethod
    async def list_subscription_plans(cls, db: AsyncSession) -> list[SubscriptionPlan]:
        await PaymentService.ensure_default_subscription_plans(db)
        await db.commit()
        result = await db.execute(select(SubscriptionPlan).order_by(SubscriptionPlan.sort_order, SubscriptionPlan.duration_days))
        return list(result.scalars().all())

    @classmethod
    async def update_subscription_plan(
        cls,
        db: AsyncSession,
        *,
        code: str,
        body: AdminSubscriptionPlanUpdateRequest,
    ) -> SubscriptionPlan:
        await PaymentService.ensure_default_subscription_plans(db)
        plan = (
            await db.execute(select(SubscriptionPlan).where(SubscriptionPlan.code == cls._normalize_code(code)))
        ).scalar_one_or_none()
        if plan is None:
            raise NotFoundError("Subscription plan not found")
        plan.name = body.name.strip()
        plan.price_amount = body.price_amount
        plan.is_active = body.is_active
        plan.sort_order = body.sort_order
        await db.commit()
        await db.refresh(plan)
        return plan

    @staticmethod
    async def get_overview(db: AsyncSession) -> PaymentOverviewRead:
        totals = (
            await db.execute(
                select(
                    func.count(PaymentTransaction.id),
                    func.sum(case((PaymentTransaction.status == "pending", 1), else_=0)),
                    func.sum(case((PaymentTransaction.status == "paid", 1), else_=0)),
                    func.sum(case((PaymentTransaction.status == "failed", 1), else_=0)),
                    func.sum(case((PaymentTransaction.status == "cancelled", 1), else_=0)),
                    func.sum(
                        case(
                            (PaymentTransaction.status == "paid", PaymentTransaction.amount),
                            else_=0,
                        )
                    ),
                )
            )
        ).one()

        return PaymentOverviewRead(
            total_transactions=int(totals[0] or 0),
            pending_transactions=int(totals[1] or 0),
            paid_transactions=int(totals[2] or 0),
            failed_transactions=int(totals[3] or 0),
            cancelled_transactions=int(totals[4] or 0),
            paid_revenue_amount=int(totals[5] or 0),
            paid_revenue_currency="VND",
        )

    @classmethod
    async def get_revenue_stats(cls, db: AsyncSession, period: str) -> PaymentStatsRead:
        if period not in {"day", "month", "year"}:
            raise BadRequestError("Invalid stats period")

        buckets = cls._build_stat_buckets(period)
        bucket_totals = {
            bucket_start: {"paid_revenue_amount": 0, "paid_transactions": 0}
            for _, bucket_start in buckets
        }
        earliest_bucket = buckets[0][1]

        rows = (
            await db.execute(
                select(PaymentTransaction.paid_at, PaymentTransaction.amount)
                .where(PaymentTransaction.status == "paid")
                .where(PaymentTransaction.paid_at.is_not(None))
                .where(PaymentTransaction.paid_at >= earliest_bucket)
            )
        ).all()

        for paid_at, amount in rows:
            bucket_start = cls._bucket_key(paid_at, period)
            if bucket_start not in bucket_totals:
                continue
            bucket_totals[bucket_start]["paid_revenue_amount"] += int(amount or 0)
            bucket_totals[bucket_start]["paid_transactions"] += 1

        return PaymentStatsRead(
            period=period,
            currency="VND",
            items=[
                PaymentStatsBucketRead(
                    label=label,
                    period_start=bucket_start,
                    paid_revenue_amount=bucket_totals[bucket_start]["paid_revenue_amount"],
                    paid_transactions=bucket_totals[bucket_start]["paid_transactions"],
                    currency="VND",
                )
                for label, bucket_start in buckets
            ],
        )

    @classmethod
    async def get_dashboard(cls, db: AsyncSession, period: str) -> PaymentDashboardRead:
        if period not in {"day", "month", "year"}:
            raise BadRequestError("Invalid dashboard period")

        overview = await cls.get_overview(db)
        revenue_stats = await cls.get_revenue_stats(db, period)
        buckets = cls._build_stat_buckets(period)
        earliest_bucket = buckets[0][1]
        volume_totals = {bucket_start: 0 for _, bucket_start in buckets}

        volume_rows = (
            await db.execute(
                select(PaymentTransaction.created_at)
                .where(PaymentTransaction.created_at >= earliest_bucket)
            )
        ).all()
        for (created_at,) in volume_rows:
            bucket_start = cls._bucket_key(created_at, period)
            if bucket_start in volume_totals:
                volume_totals[bucket_start] += 1

        status_rows = (
            await db.execute(
                select(PaymentTransaction.status, func.count(PaymentTransaction.id))
                .group_by(PaymentTransaction.status)
            )
        ).all()
        status_totals = {status: int(count or 0) for status, count in status_rows}

        plan_rows = (
            await db.execute(
                select(
                    PaymentTransaction.plan_code,
                    func.sum(PaymentTransaction.amount),
                    func.count(PaymentTransaction.id),
                )
                .where(PaymentTransaction.status == "paid")
                .group_by(PaymentTransaction.plan_code)
            )
        ).all()

        recent_payments = (
            await db.execute(
                select(PaymentTransaction)
                .options(selectinload(PaymentTransaction.user))
                .order_by(PaymentTransaction.created_at.desc())
                .limit(10)
            )
        ).scalars().all()

        return PaymentDashboardRead(
            period=period,
            currency="VND",
            overview=overview,
            revenue_trend=revenue_stats.items,
            transaction_volume=[
                PaymentVolumeBucketRead(label=label, period_start=bucket_start, transactions=volume_totals[bucket_start])
                for label, bucket_start in buckets
            ],
            status_breakdown=[
                PaymentStatusBreakdownRead(status=status, transactions=status_totals.get(status, 0))
                for status in ("paid", "pending", "failed", "cancelled")
            ],
            plan_revenue_split=[
                PaymentPlanRevenueRead(
                    plan_code=plan_code or "Unknown",
                    paid_revenue_amount=int(revenue or 0),
                    paid_transactions=int(transactions or 0),
                    currency="VND",
                )
                for plan_code, revenue, transactions in plan_rows
            ],
            recent_payments=[serialize_admin_payment_transaction(payment) for payment in recent_payments],
        )

    @staticmethod
    async def list_transactions(
        db: AsyncSession,
        *,
        status: str | None,
        search: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[PaymentTransaction], int]:
        stmt = (
            select(PaymentTransaction)
            .join(User, PaymentTransaction.user_id == User.id)
            .options(selectinload(PaymentTransaction.user))
        )
        count_stmt = select(func.count(PaymentTransaction.id)).join(User, PaymentTransaction.user_id == User.id)

        if status:
            stmt = stmt.where(PaymentTransaction.status == status)
            count_stmt = count_stmt.where(PaymentTransaction.status == status)

        if search:
            search_term = f"%{search.strip()}%"
            search_filter = or_(
                PaymentTransaction.order_code.ilike(search_term),
                PaymentTransaction.external_checkout_id.ilike(search_term),
                PaymentTransaction.external_transaction_id.ilike(search_term),
                PaymentTransaction.failure_reason.ilike(search_term),
                User.email.ilike(search_term),
                User.display_name.ilike(search_term),
            )
            stmt = stmt.where(search_filter)
            count_stmt = count_stmt.where(search_filter)

        stmt = stmt.order_by(PaymentTransaction.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

        items = (await db.execute(stmt)).scalars().all()
        total = int((await db.execute(count_stmt)).scalar_one() or 0)
        return items, total

    @staticmethod
    async def get_transaction(db: AsyncSession, payment_id: int) -> PaymentTransaction:
        payment = (
            await db.execute(
                select(PaymentTransaction)
                .options(selectinload(PaymentTransaction.user))
                .where(PaymentTransaction.id == payment_id)
            )
        ).scalar_one_or_none()
        if payment is None:
            raise NotFoundError("Payment transaction not found")
        return payment

    @classmethod
    async def approve_transaction(
        cls,
        db: AsyncSession,
        *,
        payment_id: int,
        reason: str | None,
    ) -> PaymentTransaction:
        payment = await cls.get_transaction(db, payment_id)
        if payment.status == "paid":
            return payment

        await PaymentService.mark_payment_paid(
            db,
            payment=payment,
            external_transaction_id=payment.external_transaction_id or f"manual-{payment.id}",
            provider_payload={
                **(payment.provider_payload or {}),
                "manual_review": {
                    "approved": True,
                    "reason": reason or "Manual admin approval",
                },
            },
            paid_at=datetime.now(timezone.utc),
        )
        await db.commit()
        return await cls.get_transaction(db, payment_id)

    @classmethod
    async def cancel_transaction(
        cls,
        db: AsyncSession,
        *,
        payment_id: int,
        reason: str | None,
    ) -> PaymentTransaction:
        payment = await cls.get_transaction(db, payment_id)
        if payment.status == "paid":
            raise BadRequestError("Paid transactions cannot be cancelled from admin. Implement refund flow instead.")

        await PaymentService.mark_payment_failed(
            db,
            payment=payment,
            reason=reason or "Cancelled by admin",
            provider_payload={
                **(payment.provider_payload or {}),
                "manual_review": {
                    "cancelled": True,
                    "reason": reason or "Cancelled by admin",
                },
            },
            status="cancelled",
        )
        await db.commit()
        return await cls.get_transaction(db, payment_id)

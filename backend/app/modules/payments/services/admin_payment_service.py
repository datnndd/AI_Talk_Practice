from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.payments.models import PaymentTransaction
from app.modules.payments.schemas.admin_payment import PaymentOverviewRead
from app.modules.payments.services.payment_service import PaymentService
from app.modules.users.models.user import User


class AdminPaymentService:
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
            paid_revenue_usd_cents=int(totals[5] or 0),
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

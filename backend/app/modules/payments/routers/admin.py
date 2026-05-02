from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.payments.schemas.admin_payment import (
    AdminPaymentListResponse,
    AdminPromotionCodeCreateRequest,
    AdminPromotionCodeRead,
    AdminPromotionCodeUpdateRequest,
    AdminPaymentStatusUpdateRequest,
    AdminPaymentTransactionRead,
    AdminSubscriptionPlanRead,
    AdminSubscriptionPlanUpdateRequest,
    PaymentOverviewRead,
)
from app.modules.payments.serializers import serialize_admin_payment_transaction
from app.modules.payments.services.admin_payment_service import AdminPaymentService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/payments", tags=["admin"])


@router.get("/plans", response_model=list[AdminSubscriptionPlanRead])
async def list_subscription_plans(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminPaymentService.list_subscription_plans(db)


@router.put("/plans/{code}", response_model=AdminSubscriptionPlanRead)
async def update_subscription_plan(
    code: str,
    body: AdminSubscriptionPlanUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminPaymentService.update_subscription_plan(db, code=code, body=body)


@router.get("/promotions", response_model=list[AdminPromotionCodeRead])
async def list_promotion_codes(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminPaymentService.list_promotion_codes(db)


@router.post("/promotions", response_model=AdminPromotionCodeRead)
async def create_promotion_code(
    body: AdminPromotionCodeCreateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminPaymentService.create_promotion_code(db, body=body)


@router.put("/promotions/{code}", response_model=AdminPromotionCodeRead)
async def update_promotion_code(
    code: str,
    body: AdminPromotionCodeUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminPaymentService.update_promotion_code(db, code=code, body=body)


@router.get("/overview", response_model=PaymentOverviewRead)
async def get_payment_overview(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminPaymentService.get_overview(db)


@router.get("/transactions", response_model=AdminPaymentListResponse)
async def list_payment_transactions(
    status: str | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    items, total = await AdminPaymentService.list_transactions(
        db,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )
    return AdminPaymentListResponse(
        items=[serialize_admin_payment_transaction(item) for item in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/transactions/{payment_id}", response_model=AdminPaymentTransactionRead)
async def get_payment_transaction(
    payment_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    payment = await AdminPaymentService.get_transaction(db, payment_id)
    return serialize_admin_payment_transaction(payment)


@router.post("/transactions/{payment_id}/approve", response_model=AdminPaymentTransactionRead)
async def approve_payment_transaction(
    payment_id: int,
    body: AdminPaymentStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    payment = await AdminPaymentService.approve_transaction(
        db,
        payment_id=payment_id,
        reason=body.reason,
    )
    return serialize_admin_payment_transaction(payment)


@router.post("/transactions/{payment_id}/cancel", response_model=AdminPaymentTransactionRead)
async def cancel_payment_transaction(
    payment_id: int,
    body: AdminPaymentStatusUpdateRequest,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    payment = await AdminPaymentService.cancel_transaction(
        db,
        payment_id=payment_id,
        reason=body.reason,
    )
    return serialize_admin_payment_transaction(payment)

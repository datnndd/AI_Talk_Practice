from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.gamification.schemas.admin_gamification import (
    AdminGamificationOverviewRead,
    AdminShopProductRead,
    AdminShopProductWrite,
    AdminShopRedemptionRead,
    AdminShopRedemptionStatusUpdate,
    GamificationSettingsRead,
    GamificationSettingsUpdateRequest,
)
from app.modules.gamification.services.admin_gamification_service import AdminGamificationService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/gamification", tags=["admin"])


@router.get("/shop/products", response_model=list[AdminShopProductRead])
async def list_admin_shop_products(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.list_shop_products(db)


@router.post("/shop/products", response_model=AdminShopProductRead, status_code=201)
async def create_admin_shop_product(
    body: AdminShopProductWrite,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.create_shop_product(db, body)


@router.put("/shop/products/{product_id}", response_model=AdminShopProductRead)
async def update_admin_shop_product(
    product_id: int,
    body: AdminShopProductWrite,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.update_shop_product(db, product_id, body)


@router.delete("/shop/products/{product_id}", response_model=AdminShopProductRead)
async def hide_admin_shop_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.hide_shop_product(db, product_id)


@router.get("/shop/redemptions", response_model=list[AdminShopRedemptionRead])
async def list_admin_shop_redemptions(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.list_shop_redemptions(db)


@router.put("/shop/redemptions/{redemption_id}/status", response_model=AdminShopRedemptionRead)
async def update_admin_shop_redemption_status(
    redemption_id: int,
    body: AdminShopRedemptionStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.update_shop_redemption_status(db, redemption_id, body)


@router.get("/settings", response_model=GamificationSettingsRead)
async def get_admin_gamification_settings(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.get_settings(db)


@router.put("/settings", response_model=GamificationSettingsRead)
async def update_admin_gamification_settings(
    body: GamificationSettingsUpdateRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin_user),
):
    return await AdminGamificationService.update_settings(db, actor=actor, body=body)


@router.get("/overview", response_model=AdminGamificationOverviewRead)
async def get_admin_gamification_overview(
    date_: date | None = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.get_overview(db, target_date=date_ or date.today())

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.gamification.schemas import (
    CheckInResponse,
    GamificationDashboard,
    LeaderboardPeriod,
    LeaderboardRead,
    ShopPurchaseRequest,
    ShopPurchaseResponse,
    ShopRead,
)
from app.modules.gamification.services import GamificationService
from app.modules.users.models.user import User

router = APIRouter(prefix="/gamification", tags=["gamification"])


@router.get("/me", response_model=GamificationDashboard)
async def get_my_gamification(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GamificationService.get_dashboard(db, user)


@router.get("/leaderboard", response_model=LeaderboardRead)
async def get_leaderboard(
    period: LeaderboardPeriod = Query(default="weekly"),
    limit: int = Query(default=5, ge=3, le=20),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GamificationService.get_leaderboard(db, user, period=period, limit=limit)


@router.post("/check-in", response_model=CheckInResponse)
async def check_in(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GamificationService.check_in(db, user)


@router.get("/shop", response_model=ShopRead)
async def get_shop(
    _: User = Depends(get_current_user),
):
    return GamificationService.get_shop()


@router.post("/shop/purchase", response_model=ShopPurchaseResponse)
async def purchase_shop_item(
    body: ShopPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GamificationService.purchase_shop_item(db, user, body.item_code)

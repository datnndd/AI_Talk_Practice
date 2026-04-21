from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user, get_db
from app.modules.gamification.schemas import (
    DailyGoalUpdateRequest,
    GamificationDashboard,
    HeartPurchaseRequest,
    HeartPurchaseResponse,
    LeaderboardPeriod,
    LeaderboardRead,
    LessonCompleteRequest,
    LessonCompleteResponse,
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


@router.patch("/daily-goal", response_model=GamificationDashboard)
async def update_daily_goal(
    body: DailyGoalUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GamificationService.update_daily_goal(db, user, body.daily_xp_goal)


@router.post("/lessons/complete", response_model=LessonCompleteResponse)
async def complete_lesson(
    body: LessonCompleteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return await GamificationService.complete_lesson(db, user, body)


@router.post("/hearts/purchase", response_model=HeartPurchaseResponse)
async def purchase_hearts(
    body: HeartPurchaseRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    hearts_added, gem_spent, dashboard = await GamificationService.purchase_hearts(db, user, body.hearts)
    return HeartPurchaseResponse(hearts_added=hearts_added, gem_spent=gem_spent, dashboard=dashboard)

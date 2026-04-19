from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.gamification.schemas.admin_gamification import (
    AchievementAdminRead,
    AchievementCreateRequest,
    AchievementListResponse,
    AchievementUpdateRequest,
    AdminGamificationOverviewRead,
    GamificationSettingsRead,
    GamificationSettingsUpdateRequest,
)
from app.modules.gamification.services.admin_gamification_service import AdminGamificationService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/gamification", tags=["admin"])


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


@router.get("/achievements", response_model=AchievementListResponse)
async def list_admin_achievements(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    items = await AdminGamificationService.list_achievements(db)
    return AchievementListResponse(items=items, total=len(items))


@router.post("/achievements", response_model=AchievementAdminRead, status_code=status.HTTP_201_CREATED)
async def create_admin_achievement(
    body: AchievementCreateRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin_user),
):
    return await AdminGamificationService.create_achievement(db, actor=actor, body=body)


@router.patch("/achievements/{achievement_id}", response_model=AchievementAdminRead)
async def update_admin_achievement(
    achievement_id: int,
    body: AchievementUpdateRequest,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin_user),
):
    return await AdminGamificationService.update_achievement(
        db,
        actor=actor,
        achievement_id=achievement_id,
        body=body,
    )


@router.delete("/achievements/{achievement_id}", response_model=AchievementAdminRead)
async def delete_admin_achievement(
    achievement_id: int,
    db: AsyncSession = Depends(get_db),
    actor: User = Depends(require_admin_user),
):
    return await AdminGamificationService.delete_achievement(db, actor=actor, achievement_id=achievement_id)


@router.get("/overview", response_model=AdminGamificationOverviewRead)
async def get_admin_gamification_overview(
    date_: date | None = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.get_overview(db, target_date=date_ or date.today())

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.gamification.schemas.admin_gamification import (
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


@router.get("/overview", response_model=AdminGamificationOverviewRead)
async def get_admin_gamification_overview(
    date_: date | None = Query(default=None, alias="date"),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    return await AdminGamificationService.get_overview(db, target_date=date_ or date.today())

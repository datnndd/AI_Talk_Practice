from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, require_admin_user
from app.modules.characters.schemas import (
    CharacterCreate,
    CharacterListResponse,
    CharacterRead,
    CharacterUpdate,
)
from app.modules.characters.serializers import serialize_character
from app.modules.characters.services import CharacterService
from app.modules.users.models.user import User

router = APIRouter(prefix="/admin/characters", tags=["admin"])


@router.get("", response_model=CharacterListResponse)
async def list_admin_characters(
    search: str | None = Query(default=None),
    active_only: bool = Query(default=False),
    include_deleted: bool = Query(default=False),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    characters, total = await CharacterService.list_characters(
        db,
        search=search,
        active_only=active_only,
        include_deleted=include_deleted,
        page=page,
        page_size=page_size,
    )
    return CharacterListResponse(
        items=[serialize_character(item) for item in characters],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=CharacterRead, status_code=status.HTTP_201_CREATED)
async def create_admin_character(
    body: CharacterCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    character = await CharacterService.create_character(db, body)
    return serialize_character(character)


@router.put("/{character_id}", response_model=CharacterRead)
async def update_admin_character(
    character_id: int,
    body: CharacterUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    character = await CharacterService.update_character(db, character_id, body)
    return serialize_character(character)


@router.delete("/{character_id}", response_model=CharacterRead)
async def delete_admin_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    character = await CharacterService.soft_delete_character(db, character_id)
    return serialize_character(character)


@router.post("/{character_id}/restore", response_model=CharacterRead)
async def restore_admin_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    character = await CharacterService.restore_character(db, character_id)
    return serialize_character(character)


@router.post("/{character_id}/toggle-active", response_model=CharacterRead)
async def toggle_admin_character(
    character_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin_user),
):
    character = await CharacterService.toggle_character_active(db, character_id)
    return serialize_character(character)

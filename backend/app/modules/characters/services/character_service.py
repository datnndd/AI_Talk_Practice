from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BadRequestError, NotFoundError
from app.modules.characters.models import Character
from app.modules.characters.repository import CharacterRepository
from app.modules.characters.schemas import CharacterCreate, CharacterUpdate


class CharacterService:
    @staticmethod
    async def list_characters(
        db: AsyncSession,
        *,
        search: str | None,
        active_only: bool,
        include_deleted: bool,
        page: int,
        page_size: int,
    ) -> tuple[list[Character], int]:
        return await CharacterRepository.list_characters(
            db,
            search=search,
            active_only=active_only,
            include_deleted=include_deleted,
            page=page,
            page_size=page_size,
        )

    @staticmethod
    async def get_character(db: AsyncSession, character_id: int) -> Character:
        character = await CharacterRepository.get_by_id(db, character_id, include_deleted=True)
        if character is None:
            raise NotFoundError("Character not found")
        return character

    @staticmethod
    async def ensure_active_character(db: AsyncSession, character_id: int | None) -> Character | None:
        if character_id is None:
            return None
        character = await CharacterRepository.get_by_id(db, character_id)
        if character is None or not character.is_active:
            raise BadRequestError("Selected character is not active or does not exist")
        return character

    @classmethod
    async def create_character(cls, db: AsyncSession, body: CharacterCreate) -> Character:
        character = await CharacterRepository.create(
            db,
            name=body.name.strip(),
            description=(body.description or "").strip() or None,
            model_url=body.model_url.strip(),
            core_url=body.core_url.strip(),
            thumbnail_url=(body.thumbnail_url or "").strip() or None,
            tts_voice=body.tts_voice.strip(),
            tts_language=body.tts_language.strip(),
            is_active=body.is_active,
            sort_order=body.sort_order,
            character_metadata=body.metadata or {},
        )
        await db.commit()
        return await cls.get_character(db, character.id)

    @classmethod
    async def update_character(cls, db: AsyncSession, character_id: int, body: CharacterUpdate) -> Character:
        character = await cls.get_character(db, character_id)
        update_data = body.model_dump(exclude_unset=True)
        metadata = update_data.pop("metadata", None)
        if metadata is not None:
            character.character_metadata = metadata

        for key, value in update_data.items():
            if isinstance(value, str):
                value = value.strip()
                if key in {"description", "thumbnail_url"} and not value:
                    value = None
            setattr(character, key, value)

        await db.commit()
        return await cls.get_character(db, character.id)

    @classmethod
    async def soft_delete_character(cls, db: AsyncSession, character_id: int) -> Character:
        character = await cls.get_character(db, character_id)
        character.deleted_at = datetime.now(timezone.utc)
        character.is_active = False
        await db.commit()
        await db.refresh(character)
        return character

    @classmethod
    async def restore_character(cls, db: AsyncSession, character_id: int) -> Character:
        character = await cls.get_character(db, character_id)
        character.deleted_at = None
        character.is_active = True
        await db.commit()
        await db.refresh(character)
        return character

    @classmethod
    async def toggle_character_active(cls, db: AsyncSession, character_id: int) -> Character:
        character = await cls.get_character(db, character_id)
        character.is_active = not character.is_active
        await db.commit()
        await db.refresh(character)
        return character

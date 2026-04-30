from __future__ import annotations

from app.modules.characters.models import Character
from app.modules.characters.schemas import CharacterRead


def serialize_character(character: Character) -> CharacterRead:
    return CharacterRead.model_validate(
        {
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "model_url": character.model_url,
            "core_url": character.core_url,
            "thumbnail_url": character.thumbnail_url,
            "tts_voice": character.tts_voice,
            "tts_language": character.tts_language,
            "is_active": character.is_active,
            "sort_order": character.sort_order,
            "metadata": character.character_metadata or {},
            "deleted_at": character.deleted_at,
            "created_at": character.created_at,
            "updated_at": character.updated_at,
        }
    )

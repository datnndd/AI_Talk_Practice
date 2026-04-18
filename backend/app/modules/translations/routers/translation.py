from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_current_user
from app.modules.translations.schemas.translation import TranslationRequest, TranslationResponse
from app.modules.translations.services.translation import TranslationService

router = APIRouter()

@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    user=Depends(get_current_user),
):
    """
    Translate text into a target language using the configured translation service.
    """
    if not request.text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Text to translate cannot be empty."
        )
    
    try:
        translated = await TranslationService.translate(
            text=request.text,
            target_language=request.target_language
        )
        return TranslationResponse(
            translated_text=translated,
            source_language=None
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Translation failed: {str(e)}"
        )

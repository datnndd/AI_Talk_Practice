import logging
from typing import Optional
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

class TranslationService:
    @staticmethod
    async def translate(text: str, target_language: str) -> str:
        """
        Translate the text into the target_language using Google Cloud Translation API.
        """
        api_key = settings.google_translate_api_key
        if not api_key:
            raise Exception("Google Translate API key is not configured. Please add GOOGLE_TRANSLATE_API_KEY to your environment.")
        
        url = "https://translation.googleapis.com/language/translate/v2"
        params = {
            "key": api_key,
            "q": text,
            "target": target_language,
            "format": "text"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=params, timeout=10.0)
                
            response.raise_for_status()
            data = response.json()
            
            # The v2 API returns data.translations[0].translatedText
            translated_text = data.get("data", {}).get("translations", [{}])[0].get("translatedText")
            if not translated_text:
                raise Exception("Invalid response format from Google Translate API.")
                
            return translated_text
            
        except httpx.HTTPStatusError as e:
            logger.error(f"Google Translate HTTP error: {e.response.text}")
            raise Exception(f"Google Translate API error: {e.response.status_code}") from e
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise Exception("Failed to translate text.") from e

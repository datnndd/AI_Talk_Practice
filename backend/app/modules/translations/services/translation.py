import logging

from httpx import Timeout

logger = logging.getLogger(__name__)


class TranslationService:
    @staticmethod
    async def translate(text: str, target_language: str) -> str:
        """
        Translate text into target_language using googletrans.
        """
        try:
            from googletrans import Translator

            async with Translator(timeout=Timeout(10.0)) as translator:
                result = await translator.translate(text, dest=target_language)

            translated_text = getattr(result, "text", None)
            if not translated_text:
                raise Exception("Invalid response format from googletrans.")

            return translated_text
        except ImportError as e:
            logger.error("googletrans is not installed.")
            raise Exception("googletrans is not installed. Install backend requirements.") from e
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            raise Exception("Failed to translate text.") from e

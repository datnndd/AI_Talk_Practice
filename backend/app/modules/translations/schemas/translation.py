from pydantic import BaseModel, Field

class TranslationRequest(BaseModel):
    text: str = Field(..., description="The text to translate")
    target_language: str = Field(..., description="The target language code (e.g. 'vi', 'en')")

class TranslationResponse(BaseModel):
    translated_text: str = Field(..., description="The translated text")
    source_language: str | None = Field(None, description="The detected source language code")

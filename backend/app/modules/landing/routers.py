from __future__ import annotations

from fastapi import APIRouter

from app.modules.landing.schemas import (
    PronunciationAssessmentConfigResponse,
    PronunciationAssessmentRequest,
    PronunciationAssessmentResponse,
)
from app.modules.landing.services import (
    LANDING_PRONUNCIATION_TEXT,
    assess_landing_pronunciation,
    pronunciation_assessment_config,
)

router = APIRouter(prefix="/landing/pronunciation-assessment", tags=["landing"])


@router.get("", response_model=PronunciationAssessmentConfigResponse)
async def get_pronunciation_assessment_config():
    return PronunciationAssessmentConfigResponse(**pronunciation_assessment_config())


@router.post("/score", response_model=PronunciationAssessmentResponse)
async def score_landing_pronunciation(body: PronunciationAssessmentRequest):
    assessment = await assess_landing_pronunciation(audio_base64=body.audio_base64)
    return PronunciationAssessmentResponse(
        reference_text=LANDING_PRONUNCIATION_TEXT,
        **assessment,
    )

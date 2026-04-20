"""Deprecated lesson endpoints kept for short-term route compatibility."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.exceptions import BadRequestError
from app.modules.sessions.schemas.lesson import (
    LessonGenerateRequest,
    LessonHintRead,
    LessonHintRequest,
    LessonNextQuestionRequest,
    LessonStateRead,
)

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.post("/generate", response_model=LessonStateRead)
async def generate_lesson(_: LessonGenerateRequest):
    raise BadRequestError("Legacy lesson runtime has been retired. Start a realtime conversation session instead.")


@router.post("/next-question", response_model=LessonStateRead)
async def next_question(_: LessonNextQuestionRequest):
    raise BadRequestError("Legacy lesson runtime has been retired. The websocket conversation flow now drives turns automatically.")


@router.post("/hint", response_model=LessonHintRead)
async def build_hint(_: LessonHintRequest):
    raise BadRequestError("Legacy lesson hints have been retired. Use POST /sessions/{session_id}/hint instead.")

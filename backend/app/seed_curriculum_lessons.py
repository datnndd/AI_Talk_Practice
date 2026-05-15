"""
Fill every curriculum unit with 12 vocabulary-related lessons and TTS audio.

Run: python -m app.seed_curriculum_lessons
"""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Any

from sqlalchemy import func, select

import app.db.models  # noqa: F401
from app.core.exceptions import BadRequestError
from app.db.session import AsyncSessionLocal
from app.infra.contracts import TTSConfig
from app.infra.factory import create_tts
from app.modules.curriculum.models import Lesson, Unit
from app.modules.curriculum.services import AdminCurriculumService
from app.core.config import settings


LESSONS_PER_UNIT = 12


@dataclass(frozen=True)
class VocabularyItem:
    word: str
    meaning_vi: str
    definition: str
    sentence: str
    question: str
    hints: tuple[str, str, str]
    distractors: tuple[tuple[str, str], tuple[str, str], tuple[str, str]]


CORE_VOCABULARY: tuple[VocabularyItem, ...] = (
    VocabularyItem(
        "reservation",
        "đặt chỗ",
        "A booking made before you arrive.",
        "I have a reservation for tonight.",
        "When do you usually make a reservation?",
        ("I make a reservation before a trip.", "I reserve a table online.", "I call the hotel first."),
        (("reception", "lễ tân"), ("recommendation", "gợi ý"), ("restaurant", "nhà hàng")),
    ),
    VocabularyItem(
        "appointment",
        "cuộc hẹn",
        "A planned meeting at a specific time.",
        "My appointment is at three o'clock.",
        "How do you confirm an appointment?",
        ("I send a message.", "I check the time again.", "I call the office."),
        (("apartment", "căn hộ"), ("agreement", "thỏa thuận"), ("announcement", "thông báo")),
    ),
    VocabularyItem(
        "receipt",
        "hóa đơn",
        "A paper or message showing that you paid.",
        "Could I have a receipt, please?",
        "Why do people keep receipts?",
        ("They need proof of payment.", "They may return items.", "They track spending."),
        (("recipe", "công thức"), ("refund", "hoàn tiền"), ("request", "yêu cầu")),
    ),
    VocabularyItem(
        "available",
        "có sẵn",
        "Ready for use or free at a certain time.",
        "Is this room available tomorrow?",
        "What do you ask when checking availability?",
        ("I ask if it is free.", "I ask about dates.", "I ask about times."),
        (("comfortable", "thoải mái"), ("expensive", "đắt"), ("crowded", "đông đúc")),
    ),
    VocabularyItem(
        "recommendation",
        "gợi ý",
        "Advice about what someone should choose.",
        "Do you have any recommendations?",
        "Who gives you good recommendations?",
        ("My friends do.", "Staff can help me.", "Online reviews help."),
        (("reservation", "đặt chỗ"), ("direction", "chỉ đường"), ("receipt", "hóa đơn")),
    ),
    VocabularyItem(
        "direction",
        "chỉ dẫn",
        "Information that helps you find a place.",
        "Could you give me directions to the station?",
        "When do you ask for directions?",
        ("When I am lost.", "When maps are unclear.", "When I visit a new place."),
        (("discount", "giảm giá"), ("distance", "khoảng cách"), ("decision", "quyết định")),
    ),
    VocabularyItem(
        "discount",
        "giảm giá",
        "A lower price than usual.",
        "Is there a discount for students?",
        "Where do you look for discounts?",
        ("I check apps.", "I ask the cashier.", "I look online."),
        (("deposit", "tiền đặt cọc"), ("direction", "chỉ dẫn"), ("delivery", "giao hàng")),
    ),
    VocabularyItem(
        "delivery",
        "giao hàng",
        "The act of bringing something to someone.",
        "The delivery should arrive this afternoon.",
        "What information is needed for delivery?",
        ("They need my address.", "They need my phone number.", "They need delivery time."),
        (("delay", "chậm trễ"), ("discount", "giảm giá"), ("departure", "khởi hành")),
    ),
    VocabularyItem(
        "departure",
        "khởi hành",
        "The time when a trip begins.",
        "Our departure time is six thirty.",
        "How do you check a departure time?",
        ("I check my ticket.", "I check the screen.", "I check the app."),
        (("arrival", "đến nơi"), ("delivery", "giao hàng"), ("destination", "điểm đến")),
    ),
    VocabularyItem(
        "arrival",
        "đến nơi",
        "The time when someone reaches a place.",
        "What is your arrival time?",
        "Who do you tell about your arrival?",
        ("I tell my family.", "I message my friend.", "I inform the hotel."),
        (("departure", "khởi hành"), ("address", "địa chỉ"), ("available", "có sẵn")),
    ),
    VocabularyItem(
        "address",
        "địa chỉ",
        "Details that show where a place is.",
        "Please write your address here.",
        "When do you need to share your address?",
        ("For delivery.", "For a taxi.", "For registration."),
        (("arrival", "đến nơi"), ("advice", "lời khuyên"), ("appointment", "cuộc hẹn")),
    ),
    VocabularyItem(
        "refund",
        "hoàn tiền",
        "Money returned after a problem with a purchase.",
        "Can I get a refund for this ticket?",
        "Why might someone ask for a refund?",
        ("The item is broken.", "The plan changed.", "The service was canceled."),
        (("receipt", "hóa đơn"), ("request", "yêu cầu"), ("review", "đánh giá")),
    ),
)


TOPIC_KEYWORDS: dict[str, tuple[str, ...]] = {
    "hotel": ("reservation", "available", "reception", "address", "arrival", "departure"),
    "travel": ("departure", "arrival", "direction", "destination", "available", "reservation"),
    "shop": ("discount", "receipt", "refund", "available", "delivery", "recommendation"),
    "restaurant": ("reservation", "recommendation", "receipt", "available", "delivery", "discount"),
    "work": ("appointment", "available", "recommendation", "request", "decision", "schedule"),
}


def _slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _vocabulary_for_unit(unit_title: str) -> list[VocabularyItem]:
    slug = _slug(unit_title)
    preferred_words: list[str] = []
    for keyword, words in TOPIC_KEYWORDS.items():
        if keyword in slug:
            preferred_words.extend(words)
    ordered = []
    seen = set()
    for word in preferred_words:
        for item in CORE_VOCABULARY:
            if item.word == word and item.word not in seen:
                ordered.append(item)
                seen.add(item.word)
    for item in CORE_VOCABULARY:
        if item.word not in seen:
            ordered.append(item)
            seen.add(item.word)
    return ordered[:LESSONS_PER_UNIT]


async def _tts_url(db, text: str) -> str:
    last_error: Exception | None = None
    for attempt in range(6):
        try:
            await asyncio.sleep(1.5 + attempt)
            tts = create_tts(settings)
            chunks: list[bytes] = []
            try:
                async for chunk in tts.synthesize(
                    text,
                    TTSConfig(
                        voice="Cherry",
                        language="en",
                        instructions="Read clearly in natural American English for language learners.",
                    ),
                ):
                    if chunk:
                        chunks.append(chunk)
            finally:
                await tts.close()
            asset = await AdminCurriculumService._create_audio_asset(
                db,
                source="tts",
                audio_bytes=b"".join(chunks),
                content_type="audio/wav",
                text=text,
                voice="Cherry",
                language="en",
                extension="wav",
            )
            return asset.url
        except BadRequestError as exc:
            last_error = exc
            if "empty" not in str(exc).lower():
                raise
            await asyncio.sleep(2 + attempt)
    raise last_error or BadRequestError("Lesson audio was empty")


async def _lesson_payload(db, item: VocabularyItem, index: int) -> dict[str, Any]:
    lesson_type = ("definition_choice", "shadowing", "read_aloud", "quick_qa")[index % 4]
    if lesson_type == "definition_choice":
        options = [{"word": item.word, "meaning_vi": item.meaning_vi, "is_correct": True}]
        options.extend({"word": word, "meaning_vi": meaning, "is_correct": False} for word, meaning in item.distractors)
        return {
            "type": lesson_type,
            "title": f"Vocabulary: {item.word}",
            "content": {
                "definition_text": item.definition,
                "definition_audio_url": await _tts_url(db, item.definition),
                "options": options,
            },
        }
    if lesson_type == "shadowing":
        return {
            "type": lesson_type,
            "title": f"Repeat: {item.word}",
            "content": {
                "reference_text": item.sentence,
                "meaning_vi": item.meaning_vi,
                "sample_audio_url": await _tts_url(db, item.sentence),
                "slow_audio_url": "",
            },
        }
    if lesson_type == "read_aloud":
        return {
            "type": lesson_type,
            "title": f"Read aloud: {item.word}",
            "content": {
                "text": item.sentence,
                "meaning_vi": item.meaning_vi,
                "sample_audio_url": await _tts_url(db, item.sentence),
            },
        }
    return {
        "type": lesson_type,
        "title": f"Quick Q&A: {item.word}",
        "content": {
            "question_text": item.question,
            "question_audio_url": await _tts_url(db, item.question),
            "answer_hints": list(item.hints),
            "min_words": 2,
        },
    }


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        units = (await db.execute(select(Unit).where(Unit.is_active.is_(True)).order_by(Unit.id))).scalars().all()
        if not units:
            print("No active units found.")
            return

        created = 0
        for unit in units:
            lesson_count = await db.scalar(select(func.count(Lesson.id)).where(Lesson.unit_id == unit.id)) or 0
            if lesson_count >= LESSONS_PER_UNIT:
                print(f"Unit {unit.id} already has {lesson_count} lessons. Skipped.")
                continue
            vocabulary = _vocabulary_for_unit(unit.title)
            for order_index in range(int(lesson_count), LESSONS_PER_UNIT):
                payload = await _lesson_payload(db, vocabulary[order_index], order_index)
                lesson = Lesson(
                    unit_id=unit.id,
                    type=payload["type"],
                    title=payload["title"],
                    order_index=order_index,
                    content=payload["content"],
                    pass_score=80,
                    is_active=True,
                )
                db.add(lesson)
                await db.commit()
                created += 1
                print(f"Created lesson {order_index + 1}/12 for unit {unit.id}: {lesson.title}")
        print(f"Done. Created {created} lessons.")


if __name__ == "__main__":
    asyncio.run(seed())

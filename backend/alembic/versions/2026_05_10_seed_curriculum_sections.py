"""seed six curriculum sections

Revision ID: 2026_05_10_seed_curriculum_sections
Revises: 2026_05_10_remove_dictionary_audio_cache
Create Date: 2026-05-10 02:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_seed_curriculum_sections"
down_revision: Union[str, None] = "2026_05_10_remove_dictionary_audio_cache"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


SECTIONS = [
    {
        "code": "A1_DAILY",
        "title": "A1 Daily Survival",
        "cefr_level": "A1",
        "description": "Practice simple English for greetings, food, shopping, and everyday questions.",
        "order_index": 0,
        "is_active": True,
    },
    {
        "code": "A1_TRAVEL",
        "title": "A1 Travel Basics",
        "cefr_level": "A1",
        "description": "Learn basic phrases for airports, hotels, directions, and restaurants.",
        "order_index": 1,
        "is_active": True,
    },
    {
        "code": "A2_SOCIAL",
        "title": "A2 Social Conversations",
        "cefr_level": "A2",
        "description": "Build confidence talking about yourself, routines, hobbies, and simple opinions.",
        "order_index": 2,
        "is_active": True,
    },
    {
        "code": "A2_PROBLEM_SOLVING",
        "title": "A2 Problem Solving",
        "cefr_level": "A2",
        "description": "Practice asking for help, explaining problems, making requests, and handling service situations.",
        "order_index": 3,
        "is_active": True,
    },
    {
        "code": "B1_WORK",
        "title": "B1 Workplace Speaking",
        "cefr_level": "B1",
        "description": "Practice meetings, updates, small talk, scheduling, and clear workplace communication.",
        "order_index": 4,
        "is_active": True,
    },
    {
        "code": "B1_OPINIONS",
        "title": "B1 Confident Opinions",
        "cefr_level": "B1",
        "description": "Learn to explain opinions, give reasons, compare choices, and answer follow-up questions.",
        "order_index": 5,
        "is_active": True,
    },
]


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_table(sa.inspect(bind), "learning_sections"):
        return
    for section in SECTIONS:
        existing_id = bind.execute(
            sa.text("SELECT id FROM learning_sections WHERE code = :code"),
            {"code": section["code"]},
        ).scalar_one_or_none()
        if existing_id is None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO learning_sections (code, title, cefr_level, description, order_index, is_active)
                    VALUES (:code, :title, :cefr_level, :description, :order_index, :is_active)
                    """
                ),
                section,
            )
        else:
            bind.execute(
                sa.text(
                    """
                    UPDATE learning_sections
                    SET title = :title, cefr_level = :cefr_level, description = :description,
                        order_index = :order_index, is_active = :is_active
                    WHERE code = :code
                    """
                ),
                section,
            )


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_table(sa.inspect(bind), "learning_sections"):
        return
    bind.execute(
        sa.text("DELETE FROM learning_sections WHERE code IN :codes"),
        {"codes": tuple(section["code"] for section in SECTIONS)},
    )

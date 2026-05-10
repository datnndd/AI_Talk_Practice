"""seed curriculum units

Revision ID: 2026_05_10_seed_curriculum_units
Revises: 2026_05_10_seed_curriculum_sections
Create Date: 2026-05-10 02:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_seed_curriculum_units"
down_revision: Union[str, None] = "2026_05_10_seed_curriculum_sections"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


UNITS = [
    {
        "section_code": "A1_DAILY",
        "title": "Greetings & Introductions",
        "description": "Practice saying hello, introducing yourself, and answering simple personal questions.",
        "order_index": 0,
        "estimated_minutes": 8,
        "xp_reward": 50,
        "coin_reward": 2,
        "is_active": True,
    },
    {
        "section_code": "A1_DAILY",
        "title": "Food & Simple Orders",
        "description": "Practice ordering drinks and food with short polite phrases.",
        "order_index": 1,
        "estimated_minutes": 10,
        "xp_reward": 60,
        "coin_reward": 2,
        "is_active": True,
    },
    {
        "section_code": "A1_TRAVEL",
        "title": "Airport Basics",
        "description": "Practice check-in, baggage, boarding, and simple airport questions.",
        "order_index": 0,
        "estimated_minutes": 10,
        "xp_reward": 60,
        "coin_reward": 2,
        "is_active": True,
    },
    {
        "section_code": "A1_TRAVEL",
        "title": "Hotels & Directions",
        "description": "Practice checking in, asking for directions, and solving basic travel needs.",
        "order_index": 1,
        "estimated_minutes": 12,
        "xp_reward": 70,
        "coin_reward": 3,
        "is_active": True,
    },
    {
        "section_code": "A2_SOCIAL",
        "title": "Routines & Hobbies",
        "description": "Practice talking about your day, free time, hobbies, and preferences.",
        "order_index": 0,
        "estimated_minutes": 12,
        "xp_reward": 70,
        "coin_reward": 3,
        "is_active": True,
    },
    {
        "section_code": "A2_PROBLEM_SOLVING",
        "title": "Asking For Help",
        "description": "Practice explaining simple problems, asking for help, and making polite requests.",
        "order_index": 0,
        "estimated_minutes": 14,
        "xp_reward": 80,
        "coin_reward": 3,
        "is_active": True,
    },
    {
        "section_code": "B1_WORK",
        "title": "Meetings & Updates",
        "description": "Practice giving work updates, scheduling, small talk, and clear meeting responses.",
        "order_index": 0,
        "estimated_minutes": 15,
        "xp_reward": 90,
        "coin_reward": 4,
        "is_active": True,
    },
    {
        "section_code": "B1_OPINIONS",
        "title": "Opinions & Reasons",
        "description": "Practice giving opinions, explaining reasons, comparing options, and answering follow-up questions.",
        "order_index": 0,
        "estimated_minutes": 16,
        "xp_reward": 100,
        "coin_reward": 4,
        "is_active": True,
    },
]


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    if not _has_table(sa.inspect(bind), "learning_sections") or not _has_table(sa.inspect(bind), "units"):
        return
    for unit in UNITS:
        section_id = bind.execute(
            sa.text("SELECT id FROM learning_sections WHERE code = :code"),
            {"code": unit["section_code"]},
        ).scalar_one_or_none()
        if section_id is None:
            continue
        payload = {key: value for key, value in unit.items() if key != "section_code"}
        payload["section_id"] = section_id
        existing_id = bind.execute(
            sa.text("SELECT id FROM units WHERE section_id = :section_id AND order_index = :order_index"),
            payload,
        ).scalar_one_or_none()
        if existing_id is None:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO units (section_id, title, description, order_index, estimated_minutes, xp_reward, coin_reward, is_active)
                    VALUES (:section_id, :title, :description, :order_index, :estimated_minutes, :xp_reward, :coin_reward, :is_active)
                    """
                ),
                payload,
            )
        else:
            bind.execute(
                sa.text(
                    """
                    UPDATE units
                    SET title = :title, description = :description, estimated_minutes = :estimated_minutes,
                        xp_reward = :xp_reward, coin_reward = :coin_reward, is_active = :is_active
                    WHERE id = :id
                    """
                ),
                {**payload, "id": existing_id},
            )


def downgrade() -> None:
    bind = op.get_bind()
    if not _has_table(sa.inspect(bind), "learning_sections") or not _has_table(sa.inspect(bind), "units"):
        return
    for unit in reversed(UNITS):
        section_id = bind.execute(
            sa.text("SELECT id FROM learning_sections WHERE code = :code"),
            {"code": unit["section_code"]},
        ).scalar_one_or_none()
        if section_id is None:
            continue
        bind.execute(
            sa.text("DELETE FROM units WHERE section_id = :section_id AND order_index = :order_index AND title = :title"),
            {"section_id": section_id, "order_index": unit["order_index"], "title": unit["title"]},
        )

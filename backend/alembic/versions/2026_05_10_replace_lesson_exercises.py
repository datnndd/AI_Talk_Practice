"""replace curriculum lesson exercise types

Revision ID: 2026_05_10_replace_lesson_exercises
Revises: 2026_05_06_remove_user_daily_goal
Create Date: 2026-05-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_replace_lesson_exercises"
down_revision: Union[str, None] = "2026_05_06_remove_user_daily_goal"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


OLD_TYPES = (
    "vocab_pronunciation",
    "cloze_dictation",
    "sentence_pronunciation",
    "interactive_conversation",
    "word_audio_choice",
)
NEW_TYPES = ("shadowing", "read_aloud", "definition_choice", "quick_qa")


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _constraint_names(inspector: sa.Inspector, table_name: str) -> set[str]:
    return {item["name"] for item in inspector.get_check_constraints(table_name) if item.get("name")}


def _type_check(types: tuple[str, ...]) -> str:
    quoted = ",".join(f"'{item}'" for item in types)
    return f"type IN ({quoted})"


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_table(inspector, "lessons"):
        return
    constraints = _constraint_names(inspector, "lessons")
    if "ck_lessons_type" in constraints:
        op.drop_constraint("ck_lessons_type", "lessons", type_="check")
    bind.execute(sa.text("DELETE FROM lesson_attempts WHERE lesson_id IN (SELECT id FROM lessons WHERE type = ANY(:types))"), {"types": list(OLD_TYPES)})
    bind.execute(sa.text("DELETE FROM user_lesson_progress WHERE lesson_id IN (SELECT id FROM lessons WHERE type = ANY(:types))"), {"types": list(OLD_TYPES)})
    bind.execute(sa.text("DELETE FROM lessons WHERE type = ANY(:types)"), {"types": list(OLD_TYPES)})
    op.create_check_constraint("ck_lessons_type", "lessons", _type_check(NEW_TYPES))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_table(inspector, "lessons"):
        return
    constraints = _constraint_names(inspector, "lessons")
    if "ck_lessons_type" in constraints:
        op.drop_constraint("ck_lessons_type", "lessons", type_="check")
    bind.execute(sa.text("DELETE FROM lesson_attempts WHERE lesson_id IN (SELECT id FROM lessons WHERE type = ANY(:types))"), {"types": list(NEW_TYPES)})
    bind.execute(sa.text("DELETE FROM user_lesson_progress WHERE lesson_id IN (SELECT id FROM lessons WHERE type = ANY(:types))"), {"types": list(NEW_TYPES)})
    bind.execute(sa.text("DELETE FROM lessons WHERE type = ANY(:types)"), {"types": list(NEW_TYPES)})
    op.create_check_constraint("ck_lessons_type", "lessons", _type_check(OLD_TYPES))

"""fix corrupted vietnamese lesson text

Revision ID: 2026_05_10_fix_vietnamese_lesson_text
Revises: 2026_05_10_replace_lesson_exercises
Create Date: 2026-05-10 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_10_fix_vietnamese_lesson_text"
down_revision: Union[str, None] = "2026_05_10_replace_lesson_exercises"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


REPLACEMENTS = (
    ("B?n c? th? gi?p t?i v?i ??t ch? c?a t?i kh?ng?", "B\u1ea1n c\u00f3 th\u1ec3 gi\u00fap t\u00f4i v\u1edbi \u0111\u1eb7t ch\u1ed7 c\u1ee7a t\u00f4i kh\u00f4ng?"),
    ("T?i mu?n g?i b?a s?ng.", "T\u00f4i mu\u1ed1n g\u1ecdi b\u1eefa s\u00e1ng."),
    ("??t ch?", "\u0111\u1eb7t ch\u1ed7"),
    ("l? t?n", "l\u1ec5 t\u00e2n"),
    ("g?i ?", "g\u1ee3i \u00fd"),
    ("nh? h?ng", "nh\u00e0 h\u00e0ng"),
)

def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql" or not _has_table(sa.inspect(bind), "lessons"):
        return
    for bad, good in REPLACEMENTS:
        bind.execute(
            sa.text("UPDATE lessons SET content = replace(content::text, :bad, :good)::jsonb WHERE content::text LIKE :pattern"),
            {"bad": bad, "good": good, "pattern": f"%{bad}%"},
        )


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name != "postgresql" or not _has_table(sa.inspect(bind), "lessons"):
        return
    for bad, good in REPLACEMENTS:
        bind.execute(
            sa.text("UPDATE lessons SET content = replace(content::text, :good, :bad)::jsonb WHERE content::text LIKE :pattern"),
            {"bad": bad, "good": good, "pattern": f"%{good}%"},
        )

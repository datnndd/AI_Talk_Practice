"""remove user language fields

Revision ID: 2026_04_28_remove_user_language_fields
Revises: 2026_04_28_section_unit_lesson_dictionary_audio
Create Date: 2026-04-28 09:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_04_28_remove_user_language_fields"
down_revision: Union[str, None] = "2026_04_28_section_unit_lesson_dictionary_audio"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _existing_user_columns(inspector: sa.Inspector) -> set[str]:
    if not _has_table(inspector, "users"):
        return set()
    return {column["name"] for column in inspector.get_columns("users")}


def upgrade() -> None:
    bind = op.get_bind()
    columns = _existing_user_columns(sa.inspect(bind))
    removable_columns = [
        column_name
        for column_name in ("native_language", "target_language", "target_accent")
        if column_name in columns
    ]

    if not removable_columns:
        return

    with op.batch_alter_table("users") as batch_op:
        for column_name in removable_columns:
            batch_op.drop_column(column_name)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if not _has_table(inspector, "users"):
        return
    columns = _existing_user_columns(inspector)

    with op.batch_alter_table("users") as batch_op:
        if "native_language" not in columns:
            batch_op.add_column(sa.Column("native_language", sa.String(length=10), nullable=True))
        if "target_language" not in columns:
            batch_op.add_column(sa.Column("target_language", sa.String(length=10), nullable=True))
        if "target_accent" not in columns:
            batch_op.add_column(sa.Column("target_accent", sa.String(length=20), nullable=True))

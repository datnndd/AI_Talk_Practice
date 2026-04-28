"""Add image_url to Scenario

Revision ID: b73b03169417
Revises: 2026_04_28_section_unit_lesson_dictionary_audio
Create Date: 2026-04-28 10:20:39.120644

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'b73b03169417'
down_revision: Union[str, None] = '2026_04_28_section_unit_lesson_dictionary_audio'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_column(inspector, "scenarios", "image_url"):
        op.add_column("scenarios", sa.Column("image_url", sa.String(length=500), nullable=True))


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_column(inspector, "scenarios", "image_url"):
        op.drop_column("scenarios", "image_url")

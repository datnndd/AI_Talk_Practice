"""Remove character thumbnail URL

Revision ID: 2026_05_11_remove_character_thumbnail_url
Revises: 2026_05_11_remove_promotion_codes, 2026_05_10_remove_character_metadata
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_11_remove_character_thumbnail_url"
down_revision: Union[str, tuple[str, str], None] = (
    "2026_05_11_remove_promotion_codes",
    "2026_05_10_remove_character_metadata",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "characters" in inspector.get_table_names() and _has_column(inspector, "characters", "thumbnail_url"):
        op.drop_column("characters", "thumbnail_url")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "characters" in inspector.get_table_names() and not _has_column(inspector, "characters", "thumbnail_url"):
        op.add_column("characters", sa.Column("thumbnail_url", sa.String(length=1000), nullable=True))

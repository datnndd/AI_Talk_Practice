"""Remove unused message audio metadata

Revision ID: 2026_05_11_remove_message_audio_metadata
Revises: 2026_05_11_remove_scenario_estimated_duration
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "2026_05_11_remove_message_audio_metadata"
down_revision: Union[str, None] = "2026_05_11_remove_scenario_estimated_duration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "messages" not in inspector.get_table_names():
        return

    with op.batch_alter_table("messages") as batch_op:
        if _has_column(inspector, "messages", "audio_duration_ms"):
            batch_op.drop_column("audio_duration_ms")
        if _has_column(inspector, "messages", "asr_metadata"):
            batch_op.drop_column("asr_metadata")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "messages" not in inspector.get_table_names():
        return

    with op.batch_alter_table("messages") as batch_op:
        if not _has_column(inspector, "messages", "audio_duration_ms"):
            batch_op.add_column(sa.Column("audio_duration_ms", sa.Integer(), nullable=True))
        if not _has_column(inspector, "messages", "asr_metadata"):
            batch_op.add_column(sa.Column("asr_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

"""Remove scenario ai system prompt

Revision ID: 2026_05_12_remove_scenario_ai_system_prompt
Revises: 2026_05_11_add_message_pronunciation_scores
Create Date: 2026-05-12 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_12_remove_scenario_ai_system_prompt"
down_revision: Union[str, None] = "2026_05_11_add_message_pronunciation_scores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return table_name in inspector.get_table_names() and any(
        column["name"] == column_name for column in inspector.get_columns(table_name)
    )


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_column(inspector, "scenarios", "ai_system_prompt"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.drop_column("ai_system_prompt")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_column(inspector, "scenarios", "ai_system_prompt"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.add_column(sa.Column("ai_system_prompt", sa.Text(), nullable=False, server_default=""))

"""Drop session score pronunciation column

Revision ID: 2026_05_13_drop_session_score_pronunciation
Revises: 2026_05_13_drop_message_pronunciation_scores
Create Date: 2026-05-13 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_13_drop_session_score_pronunciation"
down_revision: Union[str, None] = "2026_05_13_drop_message_pronunciation_scores"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return table_name in inspector.get_table_names() and any(
        column["name"] == column_name for column in inspector.get_columns(table_name)
    )


def _has_check(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    return any(item.get("name") == constraint_name for item in inspector.get_check_constraints(table_name))


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if not _has_column(inspector, "session_scores", "avg_pronunciation"):
        return

    with op.batch_alter_table("session_scores") as batch_op:
        if _has_check(inspector, "session_scores", "ck_ss_pronunciation"):
            batch_op.drop_constraint("ck_ss_pronunciation", type_="check")
        batch_op.drop_column("avg_pronunciation")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_column(inspector, "session_scores", "avg_pronunciation"):
        return

    with op.batch_alter_table("session_scores") as batch_op:
        batch_op.add_column(sa.Column("avg_pronunciation", sa.Float(), nullable=False, server_default="0"))
        batch_op.create_check_constraint("ck_ss_pronunciation", "avg_pronunciation BETWEEN 0 AND 10")

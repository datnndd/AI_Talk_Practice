"""Drop session score intonation column

Revision ID: 2026_05_19_drop_session_score_intonation
Revises: 2026_05_19_remove_read_aloud_lessons
Create Date: 2026-05-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2026_05_19_drop_session_score_intonation"
down_revision: Union[str, None] = "2026_05_19_remove_read_aloud_lessons"
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
    if not _has_column(inspector, "session_scores", "avg_intonation"):
        return

    with op.batch_alter_table("session_scores") as batch_op:
        if _has_check(inspector, "session_scores", "ck_ss_intonation"):
            batch_op.drop_constraint("ck_ss_intonation", type_="check")
        batch_op.drop_column("avg_intonation")

def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if _has_column(inspector, "session_scores", "avg_intonation"):
        return

    with op.batch_alter_table("session_scores") as batch_op:
        batch_op.add_column(sa.Column("avg_intonation", sa.Float(), nullable=False, server_default="0"))
        batch_op.create_check_constraint("ck_ss_intonation", "avg_intonation BETWEEN 0 AND 10")

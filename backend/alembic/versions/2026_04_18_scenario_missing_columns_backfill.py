"""backfill missing scenario columns

Revision ID: 2026_04_18_scenario_missing_columns_backfill
Revises: 2026_04_18_scenario_static_fields
Create Date: 2026-04-18 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_18_scenario_missing_columns_backfill"
down_revision: Union[str, None] = "2026_04_18_scenario_static_fields"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("scenarios")}

    # SQLite project databases reached the previous head without these model columns.
    with op.batch_alter_table("scenarios") as batch_op:
        if "time_limit_minutes" not in existing_columns:
            batch_op.add_column(sa.Column("time_limit_minutes", sa.Integer(), nullable=True))
        if "starter" not in existing_columns:
            batch_op.add_column(
                sa.Column("starter", sa.String(length=10), nullable=False, server_default=sa.text("'AI'"))
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_columns = {column["name"] for column in inspector.get_columns("scenarios")}

    with op.batch_alter_table("scenarios") as batch_op:
        if "starter" in existing_columns:
            batch_op.drop_column("starter")
        if "time_limit_minutes" in existing_columns:
            batch_op.drop_column("time_limit_minutes")

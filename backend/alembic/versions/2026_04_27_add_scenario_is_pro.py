"""add scenario is_pro

Revision ID: 2026_04_27_add_scenario_is_pro
Revises: 2026_04_27_remove_scenario_metadata
Create Date: 2026-04-27 20:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_27_add_scenario_is_pro"
down_revision: Union[str, None] = "2026_04_27_remove_scenario_metadata"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "scenarios") and not _has_column(inspector, "scenarios", "is_pro"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.add_column(
                sa.Column("is_pro", sa.Boolean(), nullable=False, server_default="0")
            )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "scenarios") and _has_column(inspector, "scenarios", "is_pro"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.drop_column("is_pro")

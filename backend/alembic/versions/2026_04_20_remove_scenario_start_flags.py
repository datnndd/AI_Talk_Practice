"""remove scenario start flags

Revision ID: 2026_04_20_remove_scenario_start_flags
Revises: 2026_04_20_scenario_roles_columns
Create Date: 2026-04-20 18:10:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_20_remove_scenario_start_flags"
down_revision: Union[str, None] = "2026_04_20_scenario_roles_columns"
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

    if not _has_table(inspector, "scenarios"):
        return

    with op.batch_alter_table("scenarios") as batch_op:
        if _has_column(inspector, "scenarios", "starter"):
            batch_op.drop_column("starter")
        if _has_column(inspector, "scenarios", "is_ai_start_first"):
            batch_op.drop_column("is_ai_start_first")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "scenarios"):
        return

    with op.batch_alter_table("scenarios") as batch_op:
        if not _has_column(inspector, "scenarios", "is_ai_start_first"):
            batch_op.add_column(sa.Column("is_ai_start_first", sa.Boolean(), nullable=False, server_default=sa.true()))
        if not _has_column(inspector, "scenarios", "starter"):
            batch_op.add_column(sa.Column("starter", sa.String(length=10), nullable=True, server_default="AI"))

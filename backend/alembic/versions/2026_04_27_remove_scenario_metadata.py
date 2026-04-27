"""remove scenario metadata

Revision ID: 2026_04_27_remove_scenario_metadata
Revises: 2026_04_27_simplify_scenarios_tasks
Create Date: 2026-04-27 20:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2026_04_27_remove_scenario_metadata"
down_revision: Union[str, None] = "2026_04_27_simplify_scenarios_tasks"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _json_column_type(bind) -> sa.types.TypeEngine:
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB()
    return sa.JSON()


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "scenarios") and _has_column(inspector, "scenarios", "metadata"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.drop_column("metadata")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_table(inspector, "scenarios") and not _has_column(inspector, "scenarios", "metadata"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.add_column(
                sa.Column("metadata", _json_column_type(bind), nullable=True, server_default=sa.text("'{}'"))
            )

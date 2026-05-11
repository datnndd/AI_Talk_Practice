"""Remove scenario estimated duration

Revision ID: 2026_05_11_remove_scenario_estimated_duration
Revises: 2026_05_11_remove_payment_original_discount_amount
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_11_remove_scenario_estimated_duration"
down_revision: Union[str, None] = "2026_05_11_remove_payment_original_discount_amount"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "scenarios" not in inspector.get_table_names():
        return

    has_time_limit = _has_column(inspector, "scenarios", "time_limit_minutes")
    has_estimated = _has_column(inspector, "scenarios", "estimated_duration")
    if has_time_limit and has_estimated:
        bind.execute(
            sa.text(
                """
                UPDATE scenarios
                SET time_limit_minutes = CASE
                    WHEN CAST((estimated_duration + 59) / 60 AS INTEGER) < 1 THEN 1
                    ELSE CAST((estimated_duration + 59) / 60 AS INTEGER)
                END
                WHERE time_limit_minutes IS NULL AND estimated_duration IS NOT NULL
                """
            )
        )

    if has_estimated:
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.drop_column("estimated_duration")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if "scenarios" not in inspector.get_table_names():
        return

    if not _has_column(inspector, "scenarios", "estimated_duration"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.add_column(sa.Column("estimated_duration", sa.SmallInteger(), nullable=True))

    inspector = sa.inspect(bind)
    if _has_column(inspector, "scenarios", "time_limit_minutes"):
        bind.execute(
            sa.text(
                """
                UPDATE scenarios
                SET estimated_duration = time_limit_minutes * 60
                WHERE estimated_duration IS NULL AND time_limit_minutes IS NOT NULL
                """
            )
        )

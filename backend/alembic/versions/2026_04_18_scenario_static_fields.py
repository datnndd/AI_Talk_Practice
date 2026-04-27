"""add scenario static fields

Revision ID: 2026_04_18_scenario_static_fields
Revises: 2026_04_07_add_payment_transactions
Create Date: 2026-04-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_18_scenario_static_fields"
down_revision: Union[str, None] = "2026_04_07_add_payment_transactions"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.add_column(sa.Column("opening_message", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("is_ai_start_first", sa.Boolean(), nullable=False, server_default=sa.true()))


def downgrade() -> None:
    with op.batch_alter_table("scenarios") as batch_op:
        batch_op.drop_column("is_ai_start_first")
        batch_op.drop_column("opening_message")

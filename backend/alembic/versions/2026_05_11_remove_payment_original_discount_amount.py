"""Remove original and discount amount from payment transactions

Revision ID: 2026_05_11_remove_payment_original_discount_amount
Revises: 2026_05_11_nullable_notification_sender
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_11_remove_payment_original_discount_amount"
down_revision: Union[str, None] = "2026_05_11_nullable_notification_sender"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "payment_transactions" not in inspector.get_table_names():
        return
    with op.batch_alter_table("payment_transactions") as batch_op:
        if _has_column(inspector, "payment_transactions", "original_amount"):
            batch_op.drop_column("original_amount")
        if _has_column(inspector, "payment_transactions", "discount_amount"):
            batch_op.drop_column("discount_amount")


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())
    if "payment_transactions" not in inspector.get_table_names():
        return
    with op.batch_alter_table("payment_transactions") as batch_op:
        if not _has_column(inspector, "payment_transactions", "original_amount"):
            batch_op.add_column(sa.Column("original_amount", sa.Integer(), nullable=True))
        if not _has_column(inspector, "payment_transactions", "discount_amount"):
            batch_op.add_column(sa.Column("discount_amount", sa.Integer(), nullable=False, server_default="0"))

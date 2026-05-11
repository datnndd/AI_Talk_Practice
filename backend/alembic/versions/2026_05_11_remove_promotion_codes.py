"""remove promotion codes

Revision ID: 2026_05_11_remove_promotion_codes
Revises: 2026_05_10_restore_daily_checkins
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2026_05_11_remove_promotion_codes"
down_revision: Union[str, None] = "2026_05_10_restore_daily_checkins"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index.get("name") for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "payment_transactions", "ix_payment_transactions_promo_code"):
        op.drop_index("ix_payment_transactions_promo_code", table_name="payment_transactions")
    if _has_column(inspector, "payment_transactions", "promo_code"):
        op.drop_column("payment_transactions", "promo_code")
    if _has_table(inspector, "promotion_codes"):
        op.drop_table("promotion_codes")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "promotion_codes"):
        op.create_table(
            "promotion_codes",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=40), nullable=False),
            sa.Column("discount_percent", sa.Integer(), nullable=False),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("starts_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("ends_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("max_redemptions", sa.Integer(), nullable=True),
            sa.Column("redeemed_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_promotion_codes_code", "promotion_codes", ["code"], unique=True)

    if _has_table(inspector, "payment_transactions") and not _has_column(inspector, "payment_transactions", "promo_code"):
        op.add_column("payment_transactions", sa.Column("promo_code", sa.String(length=40), nullable=True))
        op.create_index("ix_payment_transactions_promo_code", "payment_transactions", ["promo_code"])

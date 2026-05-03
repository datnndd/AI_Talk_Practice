"""subscription plans and promotion codes

Revision ID: 2026_05_02_subscription_plans
Revises: 2026_05_02_shop_redemptions
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2026_05_02_subscription_plans"
down_revision: Union[str, None] = "2026_05_02_shop_redemptions"
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

    if not _has_table(inspector, "subscription_plans"):
        op.create_table(
            "subscription_plans",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=40), nullable=False),
            sa.Column("name", sa.String(length=120), nullable=False),
            sa.Column("duration_days", sa.Integer(), nullable=False),
            sa.Column("price_amount", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("currency", sa.String(length=10), nullable=False, server_default="VND"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if not _has_index(inspector, "subscription_plans", "ix_subscription_plans_code"):
        op.create_index("ix_subscription_plans_code", "subscription_plans", ["code"], unique=True)

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
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
    if not _has_index(inspector, "promotion_codes", "ix_promotion_codes_code"):
        op.create_index("ix_promotion_codes_code", "promotion_codes", ["code"], unique=True)

    for column_name, column in [
        ("plan_code", sa.Column("plan_code", sa.String(length=40), nullable=True)),
        ("duration_days", sa.Column("duration_days", sa.Integer(), nullable=True)),
        ("original_amount", sa.Column("original_amount", sa.Integer(), nullable=True)),
        ("discount_amount", sa.Column("discount_amount", sa.Integer(), nullable=False, server_default="0")),
        ("promo_code", sa.Column("promo_code", sa.String(length=40), nullable=True)),
    ]:
        if not _has_column(inspector, "payment_transactions", column_name):
            op.add_column("payment_transactions", column)

    for index_name, column_name in [
        ("ix_payment_transactions_plan_code", "plan_code"),
        ("ix_payment_transactions_promo_code", "promo_code"),
    ]:
        if not _has_index(inspector, "payment_transactions", index_name):
            op.create_index(index_name, "payment_transactions", [column_name])

    plans = [
        {"code": "PRO_30D", "name": "Pro 30 ngày", "duration_days": 30, "price_amount": 99000, "sort_order": 1},
        {"code": "PRO_6M", "name": "Pro 6 tháng", "duration_days": 180, "price_amount": 499000, "sort_order": 2},
        {"code": "PRO_1Y", "name": "Pro 1 năm", "duration_days": 365, "price_amount": 899000, "sort_order": 3},
    ]
    for plan in plans:
        bind.execute(
            sa.text(
                "INSERT INTO subscription_plans (code, name, duration_days, price_amount, currency, is_active, sort_order) "
                "SELECT CAST(:code AS VARCHAR), CAST(:name AS VARCHAR), :duration_days, :price_amount, 'VND', TRUE, :sort_order "
                "WHERE NOT EXISTS (SELECT 1 FROM subscription_plans WHERE code = CAST(:code AS VARCHAR))"
            ),
            plan,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    for index_name in ["ix_payment_transactions_promo_code", "ix_payment_transactions_plan_code"]:
        if _has_index(inspector, "payment_transactions", index_name):
            op.drop_index(index_name, table_name="payment_transactions")

    for column_name in ["promo_code", "discount_amount", "original_amount", "duration_days", "plan_code"]:
        if _has_column(inspector, "payment_transactions", column_name):
            op.drop_column("payment_transactions", column_name)

    if _has_table(inspector, "promotion_codes"):
        op.drop_table("promotion_codes")
    if _has_table(inspector, "subscription_plans"):
        op.drop_table("subscription_plans")

"""add physical shop products and redemptions

Revision ID: 2026_05_02_shop_redemptions
Revises: 2026_05_01_email_otps
Create Date: 2026-05-02 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "2026_05_02_shop_redemptions"
down_revision: Union[str, None] = "2026_05_01_email_otps"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index.get("name") for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "shop_products"):
        op.create_table(
            "shop_products",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("code", sa.String(length=80), nullable=False),
            sa.Column("name", sa.String(length=160), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("price_coin", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("image_url", sa.String(length=500), nullable=True),
            sa.Column("stock_quantity", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
            sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("code", name="uq_shop_products_code"),
        )
    inspector = sa.inspect(bind)
    if not _has_index(inspector, "shop_products", "ix_shop_products_code"):
        op.create_index("ix_shop_products_code", "shop_products", ["code"])

    if not _has_table(inspector, "shop_redemptions"):
        op.create_table(
            "shop_redemptions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("product_id", sa.Integer(), sa.ForeignKey("shop_products.id"), nullable=False),
            sa.Column("product_name", sa.String(length=160), nullable=False),
            sa.Column("price_coin", sa.Integer(), nullable=False),
            sa.Column("recipient_name", sa.String(length=160), nullable=False),
            sa.Column("phone", sa.String(length=40), nullable=False),
            sa.Column("address", sa.Text(), nullable=False),
            sa.Column("note", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
            sa.Column("refunded", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )
    inspector = sa.inspect(bind)
    for index_name, columns in {
        "ix_shop_redemptions_user_id": ["user_id"],
        "ix_shop_redemptions_product_id": ["product_id"],
        "ix_shop_redemptions_status": ["status"],
    }.items():
        if not _has_index(inspector, "shop_redemptions", index_name):
            op.create_index(index_name, "shop_redemptions", columns)

    products = sa.table(
        "shop_products",
        sa.column("code", sa.String),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("price_coin", sa.Integer),
        sa.column("image_url", sa.String),
        sa.column("stock_quantity", sa.Integer),
        sa.column("is_active", sa.Boolean),
        sa.column("sort_order", sa.Integer),
    )
    for item in [
        {"code": "cap", "name": "Mũ AI Talk", "description": "Mũ lưu niệm AI Talk Practice.", "price_coin": 300, "image_url": None, "stock_quantity": 20, "is_active": True, "sort_order": 1},
        {"code": "shirt", "name": "Áo AI Talk", "description": "Áo thun AI Talk Practice.", "price_coin": 600, "image_url": None, "stock_quantity": 20, "is_active": True, "sort_order": 2},
        {"code": "pants", "name": "Quần AI Talk", "description": "Quần thể thao AI Talk Practice.", "price_coin": 800, "image_url": None, "stock_quantity": 20, "is_active": True, "sort_order": 3},
    ]:
        exists = bind.execute(sa.text("SELECT 1 FROM shop_products WHERE code = :code"), {"code": item["code"]}).first()
        if exists is None:
            bind.execute(products.insert().values(**item))


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _has_table(inspector, "shop_redemptions"):
        op.drop_table("shop_redemptions")
    if _has_table(inspector, "shop_products"):
        op.drop_table("shop_products")

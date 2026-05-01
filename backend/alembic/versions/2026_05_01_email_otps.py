"""add email otps

Revision ID: 2026_05_01_email_otps
Revises: 2026_04_30_characters
Create Date: 2026-05-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_01_email_otps"
down_revision: Union[str, None] = "2026_04_30_characters"
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

    if not _has_table(inspector, "email_otps"):
        op.create_table(
            "email_otps",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("email", sa.String(length=255), nullable=False),
            sa.Column("code_hash", sa.String(length=255), nullable=False),
            sa.Column("purpose", sa.String(length=32), nullable=False),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        )

    inspector = sa.inspect(bind)
    if not _has_index(inspector, "email_otps", "ix_email_otps_email"):
        op.create_index("ix_email_otps_email", "email_otps", ["email"])
    if not _has_index(inspector, "email_otps", "ix_email_otps_purpose"):
        op.create_index("ix_email_otps_purpose", "email_otps", ["purpose"])
    if not _has_index(inspector, "email_otps", "ix_email_otps_email_purpose"):
        op.create_index("ix_email_otps_email_purpose", "email_otps", ["email", "purpose"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if _has_table(inspector, "email_otps"):
        op.drop_table("email_otps")

"""Add payment transaction and webhook event tables

Revision ID: 2026_04_07_add_payment_transactions
Revises: 2026_04_05_profile_sync
Create Date: 2026-04-07 09:10:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_07_add_payment_transactions"
down_revision: Union[str, None] = "2026_04_05_profile_sync"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspect_obj = sa.inspect(conn)
    existing_tables = set(inspect_obj.get_table_names())

    if "payment_transactions" not in existing_tables:
        op.create_table(
            "payment_transactions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("provider", sa.String(length=20), nullable=False),
            sa.Column("plan", sa.String(length=20), nullable=False),
            sa.Column("amount", sa.Integer(), nullable=False),
            sa.Column("currency", sa.String(length=10), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False),
            sa.Column("order_code", sa.String(length=64), nullable=False),
            sa.Column("external_checkout_id", sa.String(length=255), nullable=True),
            sa.Column("external_transaction_id", sa.String(length=255), nullable=True),
            sa.Column("payment_url", sa.Text(), nullable=True),
            sa.Column("provider_payload", sa.JSON(), nullable=True),
            sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("failure_reason", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("order_code"),
            sa.UniqueConstraint("external_checkout_id"),
            sa.UniqueConstraint("external_transaction_id"),
        )
        op.create_index("ix_payment_transactions_user_id", "payment_transactions", ["user_id"])
        op.create_index("ix_payment_transactions_provider", "payment_transactions", ["provider"])
        op.create_index("ix_payment_transactions_status", "payment_transactions", ["status"])
        op.create_index(
            "ix_payment_transactions_provider_status",
            "payment_transactions",
            ["provider", "status"],
        )

    if "payment_webhook_events" not in existing_tables:
        op.create_table(
            "payment_webhook_events",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("provider", sa.String(length=20), nullable=False),
            sa.Column("event_id", sa.String(length=255), nullable=False),
            sa.Column("event_type", sa.String(length=100), nullable=True),
            sa.Column("payload", sa.JSON(), nullable=True),
            sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
            sa.UniqueConstraint("provider", "event_id", name="uq_payment_webhook_events_provider_event_id"),
        )
        op.create_index("ix_payment_webhook_events_provider", "payment_webhook_events", ["provider"])
        op.create_index("ix_payment_webhook_events_event_id", "payment_webhook_events", ["event_id"])


def downgrade() -> None:
    conn = op.get_bind()
    inspect_obj = sa.inspect(conn)
    existing_tables = set(inspect_obj.get_table_names())

    if "payment_webhook_events" in existing_tables:
        op.drop_index("ix_payment_webhook_events_event_id", table_name="payment_webhook_events")
        op.drop_index("ix_payment_webhook_events_provider", table_name="payment_webhook_events")
        op.drop_table("payment_webhook_events")

    if "payment_transactions" in existing_tables:
        op.drop_index("ix_payment_transactions_provider_status", table_name="payment_transactions")
        op.drop_index("ix_payment_transactions_status", table_name="payment_transactions")
        op.drop_index("ix_payment_transactions_provider", table_name="payment_transactions")
        op.drop_index("ix_payment_transactions_user_id", table_name="payment_transactions")
        op.drop_table("payment_transactions")

"""add user role

Revision ID: 2026_04_27_add_user_role
Revises: 2026_04_27_remove_admin_audit_logs
Create Date: 2026-04-27 19:15:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_27_add_user_role"
down_revision: Union[str, None] = "2026_04_27_remove_admin_audit_logs"
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

    if not _has_column(inspector, "users", "role"):
        op.add_column("users", sa.Column("role", sa.String(length=20), nullable=False, server_default="user"))

    if bind.dialect.name == "postgresql":
        bind.execute(
            sa.text(
                """
                UPDATE users
                SET role = 'admin'
                WHERE preferences->>'role' = 'admin'
                   OR preferences->>'is_admin' = 'true'
                """
            )
        )
    elif bind.dialect.name == "sqlite":
        bind.execute(
            sa.text(
                """
                UPDATE users
                SET role = 'admin'
                WHERE json_extract(preferences, '$.role') = 'admin'
                   OR json_extract(preferences, '$.is_admin') = 1
                """
            )
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_column(inspector, "users", "role"):
        op.drop_column("users", "role")

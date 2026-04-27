"""Add authentication and subscription fields

Revision ID: 2026_04_05_auth_fields
Revises: None
Create Date: 2026-04-05 10:46:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import JSON

# revision identifiers, used by Alembic.
revision: str = '2026_04_05_auth_fields'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _create_current_schema_for_empty_database() -> None:
    postgresql.JSONB = JSON

    from app.db.base_class import Base
    import app.db.models  # noqa: F401 - register all ORM models

    bind = op.get_bind()
    Base.metadata.create_all(bind, checkfirst=True)


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    if 'users' not in inspector.get_table_names():
        _create_current_schema_for_empty_database()
        return

    current_columns = {col['name'] for col in inspector.get_columns('users')}
    current_indexes = {idx['name'] for idx in inspector.get_indexes('users')}

    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'auth_provider' not in current_columns:
            batch_op.add_column(sa.Column('auth_provider', sa.String(length=20), server_default='local', nullable=False))
        if 'google_id' not in current_columns:
            batch_op.add_column(sa.Column('google_id', sa.String(length=255), nullable=True))
        if 'is_email_verified' not in current_columns:
            batch_op.add_column(sa.Column('is_email_verified', sa.Boolean(), server_default=sa.false(), nullable=False))
        # Ensure password_hash is nullable for Social Login
        if 'password_hash' in current_columns:
            batch_op.alter_column('password_hash', existing_type=sa.String(length=255), nullable=True)
        # Add index and unique constraint for google_id
        if 'ix_users_google_id' not in current_indexes:
            batch_op.create_index('ix_users_google_id', ['google_id'], unique=True)

def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    if 'users' not in inspector.get_table_names():
        return

    current_columns = {col['name'] for col in inspector.get_columns('users')}
    current_indexes = {idx['name'] for idx in inspector.get_indexes('users')}

    with op.batch_alter_table('users', schema=None) as batch_op:
        if 'ix_users_google_id' in current_indexes:
            batch_op.drop_index('ix_users_google_id')
        if 'password_hash' in current_columns:
            batch_op.alter_column('password_hash', existing_type=sa.String(length=255), nullable=False)
        if 'is_email_verified' in current_columns:
            batch_op.drop_column('is_email_verified')
        if 'google_id' in current_columns:
            batch_op.drop_column('google_id')
        if 'auth_provider' in current_columns:
            batch_op.drop_column('auth_provider')

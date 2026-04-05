"""Add authentication and subscription fields

Revision ID: 2026_04_05_auth_fields
Revises: None
Create Date: 2026-04-05 10:46:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '2026_04_05_auth_fields'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('auth_provider', sa.String(length=20), server_default='local', nullable=False))
        batch_op.add_column(sa.Column('google_id', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('is_email_verified', sa.Boolean(), server_default='0', nullable=False))
        # Ensure password_hash is nullable for Social Login
        batch_op.alter_column('password_hash', existing_type=sa.String(length=255), nullable=True)
        # Add index and unique constraint for google_id
        batch_op.create_index('ix_users_google_id', ['google_id'], unique=True)

def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index('ix_users_google_id')
        batch_op.alter_column('password_hash', existing_type=sa.String(length=255), nullable=False)
        batch_op.drop_column('is_email_verified')
        batch_op.drop_column('google_id')
        batch_op.drop_column('auth_provider')

"""Sync user profile fields and missing columns

Revision ID: 2026_04_05_profile_sync
Revises: 2026_04_05_auth_fields
Create Date: 2026-04-05 11:11:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '2026_04_05_profile_sync'
down_revision: Union[str, None] = '2026_04_05_auth_fields'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Get current columns
    conn = op.get_bind()
    inspect_obj = sa.inspect(conn)
    current_columns = [col['name'] for col in inspect_obj.get_columns('users')]
    
    # Use batch_alter_table for SQLite compatibility
    with op.batch_alter_table('users', schema=None) as batch_op:
        # Profile fields
        if 'display_name' not in current_columns:
            batch_op.add_column(sa.Column('display_name', sa.String(length=100), nullable=True))
        if 'avatar' not in current_columns:
            batch_op.add_column(sa.Column('avatar', sa.String(length=500), nullable=True))
        if 'age' not in current_columns:
            batch_op.add_column(sa.Column('age', sa.SmallInteger(), nullable=True))
        
        # English practice fields
        if 'native_language' not in current_columns:
            batch_op.add_column(sa.Column('native_language', sa.String(length=10), nullable=True))
        if 'target_language' not in current_columns:
            batch_op.add_column(sa.Column('target_language', sa.String(length=10), nullable=True))
        if 'target_accent' not in current_columns:
            batch_op.add_column(sa.Column('target_accent', sa.String(length=20), nullable=True))
        if 'level' not in current_columns:
            batch_op.add_column(sa.Column('level', sa.String(length=20), nullable=True))
        if 'current_cefr' not in current_columns:
            batch_op.add_column(sa.Column('current_cefr', sa.String(length=10), nullable=True))
        
        # Progress & Streak
        if 'current_streak' not in current_columns:
            batch_op.add_column(sa.Column('current_streak', sa.Integer(), server_default='0', nullable=False))
        if 'longest_streak' not in current_columns:
            batch_op.add_column(sa.Column('longest_streak', sa.Integer(), server_default='0', nullable=False))
        if 'total_practice_minutes' not in current_columns:
            batch_op.add_column(sa.Column('total_practice_minutes', sa.Integer(), server_default='0', nullable=False))
        
        # Onboarding data
        if 'favorite_topics' not in current_columns:
            batch_op.add_column(sa.Column('favorite_topics', sa.JSON(), nullable=True))
        if 'learning_purpose' not in current_columns:
            batch_op.add_column(sa.Column('learning_purpose', sa.JSON(), nullable=True))
        if 'main_challenge' not in current_columns:
            batch_op.add_column(sa.Column('main_challenge', sa.String(length=500), nullable=True))
        if 'daily_goal' not in current_columns:
            batch_op.add_column(sa.Column('daily_goal', sa.SmallInteger(), nullable=True))
        if 'is_onboarding_completed' not in current_columns:
            batch_op.add_column(sa.Column('is_onboarding_completed', sa.Boolean(), server_default=sa.false(), nullable=False))
        
        # Preferences & Lifecycle
        if 'preferences' not in current_columns:
            batch_op.add_column(sa.Column('preferences', sa.JSON(), server_default='{}', nullable=True))
        if 'deleted_at' not in current_columns:
            batch_op.add_column(sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('deleted_at')
        batch_op.drop_column('preferences')
        batch_op.drop_column('is_onboarding_completed')
        batch_op.drop_column('daily_goal')
        batch_op.drop_column('main_challenge')
        batch_op.drop_column('learning_purpose')
        batch_op.drop_column('favorite_topics')
        batch_op.drop_column('total_practice_minutes')
        batch_op.drop_column('longest_streak')
        batch_op.drop_column('current_streak')
        batch_op.drop_column('current_cefr')
        batch_op.drop_column('level')
        batch_op.drop_column('target_accent')
        batch_op.drop_column('target_language')
        batch_op.drop_column('native_language')
        batch_op.drop_column('age')
        batch_op.drop_column('avatar')
        batch_op.drop_column('display_name')

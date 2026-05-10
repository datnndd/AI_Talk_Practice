"""merge curriculum units and daily checkins heads

Revision ID: 2026_05_10_merge_curriculum_units_and_daily_checkins
Revises: 2026_05_10_seed_curriculum_units, 2026_05_10_restore_daily_checkins
Create Date: 2026-05-10 02:30:00.000000

"""
from typing import Sequence, Union


revision: str = "2026_05_10_merge_curriculum_units_and_daily_checkins"
down_revision: Union[str, tuple[str, str], None] = (
    "2026_05_10_seed_curriculum_units",
    "2026_05_10_restore_daily_checkins",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

"""merge user language removal and scenario image migrations

Revision ID: 2026_04_28_merge_user_language_and_scenario_image
Revises: 2026_04_28_remove_user_language_fields, b73b03169417
Create Date: 2026-04-28 10:45:00.000000

"""
from typing import Sequence, Union


revision: str = "2026_04_28_merge_user_language_and_scenario_image"
down_revision: Union[str, tuple[str, str], None] = (
    "2026_04_28_remove_user_language_fields",
    "b73b03169417",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

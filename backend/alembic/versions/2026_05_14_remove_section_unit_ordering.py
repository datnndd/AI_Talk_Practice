"""Remove section and unit manual ordering

Revision ID: 2026_05_14_remove_section_unit_ordering
Revises: 2026_05_13_drop_session_score_pronunciation
Create Date: 2026-05-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2026_05_14_remove_section_unit_ordering"
down_revision: Union[str, None] = "2026_05_13_drop_session_score_pronunciation"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    return any(index["name"] == index_name for index in inspector.get_indexes(table_name))


def _has_constraint(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    constraints = inspector.get_unique_constraints(table_name) + inspector.get_check_constraints(table_name)
    return any(constraint["name"] == constraint_name for constraint in constraints)


def upgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if _has_table(inspector, "learning_sections"):
        if _has_index(inspector, "learning_sections", "ix_learning_sections_active_order"):
            op.drop_index("ix_learning_sections_active_order", table_name="learning_sections")
        if _has_constraint(inspector, "learning_sections", "ck_learning_sections_order_nonnegative"):
            op.drop_constraint("ck_learning_sections_order_nonnegative", "learning_sections", type_="check")
        if _has_column(inspector, "learning_sections", "order_index"):
            op.drop_column("learning_sections", "order_index")
        if not _has_index(sa.inspect(op.get_bind()), "learning_sections", "ix_learning_sections_active_id"):
            op.create_index("ix_learning_sections_active_id", "learning_sections", ["is_active", "id"])

    inspector = sa.inspect(op.get_bind())
    if _has_table(inspector, "units"):
        if _has_index(inspector, "units", "ix_units_section_active_order"):
            op.drop_index("ix_units_section_active_order", table_name="units")
        if _has_constraint(inspector, "units", "uq_units_section_order"):
            op.drop_constraint("uq_units_section_order", "units", type_="unique")
        if _has_constraint(inspector, "units", "ck_units_order_nonnegative"):
            op.drop_constraint("ck_units_order_nonnegative", "units", type_="check")
        if _has_column(inspector, "units", "order_index"):
            op.drop_column("units", "order_index")
        if not _has_index(sa.inspect(op.get_bind()), "units", "ix_units_section_active_id"):
            op.create_index("ix_units_section_active_id", "units", ["section_id", "is_active", "id"])


def downgrade() -> None:
    inspector = sa.inspect(op.get_bind())

    if _has_table(inspector, "units"):
        if _has_index(inspector, "units", "ix_units_section_active_id"):
            op.drop_index("ix_units_section_active_id", table_name="units")
        if not _has_column(inspector, "units", "order_index"):
            op.add_column("units", sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"))
        inspector = sa.inspect(op.get_bind())
        if not _has_constraint(inspector, "units", "ck_units_order_nonnegative"):
            op.create_check_constraint("ck_units_order_nonnegative", "units", "order_index >= 0")
        if not _has_index(inspector, "units", "ix_units_section_active_order"):
            op.create_index("ix_units_section_active_order", "units", ["section_id", "is_active", "order_index"])

    inspector = sa.inspect(op.get_bind())
    if _has_table(inspector, "learning_sections"):
        if _has_index(inspector, "learning_sections", "ix_learning_sections_active_id"):
            op.drop_index("ix_learning_sections_active_id", table_name="learning_sections")
        if not _has_column(inspector, "learning_sections", "order_index"):
            op.add_column("learning_sections", sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"))
        inspector = sa.inspect(op.get_bind())
        if not _has_constraint(inspector, "learning_sections", "ck_learning_sections_order_nonnegative"):
            op.create_check_constraint("ck_learning_sections_order_nonnegative", "learning_sections", "order_index >= 0")
        if not _has_index(inspector, "learning_sections", "ix_learning_sections_active_order"):
            op.create_index("ix_learning_sections_active_order", "learning_sections", ["is_active", "order_index"])

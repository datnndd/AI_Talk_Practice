"""remove scenario variations

Revision ID: 2026_04_19_remove_scenario_variations
Revises: 2026_04_18_scenario_missing_columns_backfill
Create Date: 2026-04-19 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_19_remove_scenario_variations"
down_revision: Union[str, None] = "2026_04_18_scenario_missing_columns_backfill"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector: sa.Inspector, table_name: str, index_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _has_check_constraint(inspector: sa.Inspector, table_name: str, constraint_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return constraint_name in {constraint["name"] for constraint in inspector.get_check_constraints(table_name)}


def _cleanup_sqlite_batch_temp_table(bind: sa.Connection, table_name: str) -> None:
    if bind.dialect.name != "sqlite":
        return
    op.execute(sa.text(f'DROP TABLE IF EXISTS "_alembic_tmp_{table_name}"'))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_column(inspector, "sessions", "variation_id"):
        if _has_index(inspector, "sessions", "ix_sessions_variation_id"):
            op.drop_index("ix_sessions_variation_id", table_name="sessions")
        _cleanup_sqlite_batch_temp_table(bind, "sessions")
        with op.batch_alter_table("sessions") as batch_op:
            batch_op.drop_column("variation_id")

    if _has_table(inspector, "scenario_variations"):
        op.drop_table("scenario_variations")

    scenario_columns = {column["name"] for column in inspector.get_columns("scenarios")}
    _cleanup_sqlite_batch_temp_table(bind, "scenarios")
    with op.batch_alter_table("scenarios") as batch_op:
        if _has_check_constraint(inspector, "scenarios", "ck_scenarios_pre_gen_count_non_negative"):
            batch_op.drop_constraint("ck_scenarios_pre_gen_count_non_negative", type_="check")
        if "pre_gen_count" in scenario_columns:
            batch_op.drop_column("pre_gen_count")
        if "is_pre_generated" in scenario_columns:
            batch_op.drop_column("is_pre_generated")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "scenarios", "is_pre_generated"):
        _cleanup_sqlite_batch_temp_table(bind, "scenarios")
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.add_column(sa.Column("is_pre_generated", sa.Boolean(), nullable=False, server_default=sa.text("0")))
            batch_op.add_column(sa.Column("pre_gen_count", sa.Integer(), nullable=False, server_default=sa.text("8")))
            batch_op.create_check_constraint(
                "ck_scenarios_pre_gen_count_non_negative",
                sa.text("pre_gen_count >= 0"),
            )

    if not _has_table(inspector, "scenario_variations"):
        op.create_table(
            "scenario_variations",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("scenario_id", sa.Integer(), sa.ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False),
            sa.Column("variation_name", sa.String(length=160), nullable=True),
            sa.Column("variation_seed", sa.String(length=128), nullable=False),
            sa.Column("parameters", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
            sa.Column("sample_prompt", sa.Text(), nullable=True),
            sa.Column("sample_conversation", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
            sa.Column("system_prompt_override", sa.Text(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
            sa.Column("is_pregenerated", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("is_approved", sa.Boolean(), nullable=False, server_default=sa.text("0")),
            sa.Column("usage_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("uq_scenario_variation_seed", "scenario_variations", ["scenario_id", "variation_seed"], unique=True)
        op.create_index("ix_scenario_variations_scenario_active", "scenario_variations", ["scenario_id", "is_active"])

    if not _has_column(inspector, "sessions", "variation_id"):
        _cleanup_sqlite_batch_temp_table(bind, "sessions")
        with op.batch_alter_table("sessions") as batch_op:
            batch_op.add_column(sa.Column("variation_id", sa.Integer(), nullable=True))

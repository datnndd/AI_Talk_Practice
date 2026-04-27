"""simplify scenarios with tasks

Revision ID: 2026_04_27_simplify_scenarios_tasks
Revises: 2026_04_27_add_user_role
Create Date: 2026-04-27 19:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "2026_04_27_simplify_scenarios_tasks"
down_revision: Union[str, None] = "2026_04_27_add_user_role"
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


def _json_column_type(bind) -> sa.types.TypeEngine:
    if bind.dialect.name == "postgresql":
        return postgresql.JSONB()
    return sa.JSON()
    try:
        return constraint_name in {constraint["name"] for constraint in inspector.get_check_constraints(table_name)}
    except NotImplementedError:
        return False


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "scenarios"):
        return

    has_learning_objectives = _has_column(inspector, "scenarios", "learning_objectives")
    if not _has_column(inspector, "scenarios", "tasks"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.add_column(
                sa.Column("tasks", _json_column_type(bind), nullable=False, server_default=sa.text("'[]'"))
            )

    if has_learning_objectives:
        bind.execute(
            sa.text(
                """
                UPDATE scenarios
                SET tasks = learning_objectives
                WHERE tasks IS NULL OR CAST(tasks AS TEXT) IN ('[]', 'null', '')
                """
            )
        )

    if _has_table(inspector, "scenario_prompt_history"):
        op.drop_table("scenario_prompt_history")

    inspector = sa.inspect(bind)
    with op.batch_alter_table("scenarios") as batch_op:
        if _has_index(inspector, "scenarios", "ix_scenarios_target_skills_gin"):
            batch_op.drop_index("ix_scenarios_target_skills_gin")
        if _has_check_constraint(inspector, "scenarios", "ck_scenarios_mode"):
            batch_op.drop_constraint("ck_scenarios_mode", type_="check")
        for column_name in ("learning_objectives", "target_skills", "mode", "created_by"):
            if _has_column(inspector, "scenarios", column_name):
                batch_op.drop_column(column_name)
        if bind.dialect.name == "postgresql" and not _has_index(inspector, "scenarios", "ix_scenarios_tasks_gin"):
            batch_op.create_index("ix_scenarios_tasks_gin", ["tasks"], postgresql_using="gin")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "sessions") and _has_column(inspector, "sessions", "target_skills"):
        with op.batch_alter_table("sessions") as batch_op:
            batch_op.drop_column("target_skills")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "scenarios"):
        return

    with op.batch_alter_table("scenarios") as batch_op:
        if not _has_column(inspector, "scenarios", "learning_objectives"):
            batch_op.add_column(
                sa.Column("learning_objectives", _json_column_type(bind), nullable=True, server_default=sa.text("'[]'"))
            )
        if not _has_column(inspector, "scenarios", "target_skills"):
            batch_op.add_column(
                sa.Column("target_skills", _json_column_type(bind), nullable=True, server_default=sa.text("'[]'"))
            )
        if not _has_column(inspector, "scenarios", "mode"):
            batch_op.add_column(sa.Column("mode", sa.String(length=30), nullable=False, server_default="conversation"))
        if not _has_column(inspector, "scenarios", "created_by"):
            batch_op.add_column(sa.Column("created_by", sa.Integer(), nullable=True))
        if _has_index(inspector, "scenarios", "ix_scenarios_tasks_gin"):
            batch_op.drop_index("ix_scenarios_tasks_gin")
        if _has_column(inspector, "scenarios", "tasks"):
            batch_op.drop_column("tasks")

    inspector = sa.inspect(bind)
    if _has_table(inspector, "sessions") and not _has_column(inspector, "sessions", "target_skills"):
        with op.batch_alter_table("sessions") as batch_op:
            batch_op.add_column(sa.Column("target_skills", _json_column_type(bind), nullable=True))

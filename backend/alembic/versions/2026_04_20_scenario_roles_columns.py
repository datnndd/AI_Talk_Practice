"""move scenario roles to dedicated columns

Revision ID: 2026_04_20_scenario_roles_columns
Revises: 2026_04_20_remove_message_pronunciation_scoring
Create Date: 2026-04-20 16:40:00.000000

"""

from __future__ import annotations

import json
from typing import Any, Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2026_04_20_scenario_roles_columns"
down_revision: Union[str, None] = "2026_04_20_remove_message_pronunciation_scoring"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_table(inspector: sa.Inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector: sa.Inspector, table_name: str, column_name: str) -> bool:
    if not _has_table(inspector, table_name):
        return False
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _parse_metadata(value: Any) -> dict[str, Any]:
    if not value:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _first_text(*values: Any) -> str:
    for value in values:
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "scenarios"):
        return

    has_opening_message = _has_column(inspector, "scenarios", "opening_message")

    with op.batch_alter_table("scenarios") as batch_op:
        if not _has_column(inspector, "scenarios", "ai_role"):
            batch_op.add_column(sa.Column("ai_role", sa.String(length=500), nullable=False, server_default=""))
        if not _has_column(inspector, "scenarios", "user_role"):
            batch_op.add_column(sa.Column("user_role", sa.String(length=500), nullable=False, server_default=""))

    scenarios = sa.Table("scenarios", sa.MetaData(), autoload_with=bind)
    select_columns = [
        scenarios.c.id,
        scenarios.c.metadata,
        scenarios.c.ai_role,
        scenarios.c.user_role,
    ]
    if has_opening_message:
        select_columns.append(scenarios.c.opening_message)

    rows = bind.execute(sa.select(*select_columns)).mappings()

    for row in rows:
        metadata = _parse_metadata(row.get("metadata"))
        opening_message = _first_text(row.get("opening_message")) if has_opening_message else ""
        ai_role = _first_text(
            row.get("ai_role"),
            metadata.get("ai_role"),
            metadata.get("persona"),
            metadata.get("partner_persona"),
        )
        user_role = _first_text(
            row.get("user_role"),
            metadata.get("user_role"),
            metadata.get("learner_role"),
        )

        if opening_message and not _first_text(metadata.get("opening_message")):
            metadata["opening_message"] = opening_message

        metadata.pop("ai_role", None)
        metadata.pop("user_role", None)

        bind.execute(
            scenarios.update()
            .where(scenarios.c.id == row["id"])
            .values(
                metadata=metadata,
                ai_role=ai_role,
                user_role=user_role,
            )
        )

    inspector = sa.inspect(bind)
    if _has_column(inspector, "scenarios", "opening_message"):
        with op.batch_alter_table("scenarios") as batch_op:
            batch_op.drop_column("opening_message")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "scenarios"):
        return

    with op.batch_alter_table("scenarios") as batch_op:
        if not _has_column(inspector, "scenarios", "opening_message"):
            batch_op.add_column(sa.Column("opening_message", sa.Text(), nullable=True))

    scenarios = sa.Table("scenarios", sa.MetaData(), autoload_with=bind)
    rows = bind.execute(
        sa.select(
            scenarios.c.id,
            scenarios.c.metadata,
            scenarios.c.ai_role,
            scenarios.c.user_role,
        )
    ).mappings()

    for row in rows:
        metadata = _parse_metadata(row.get("metadata"))
        opening_message = _first_text(
            metadata.get("opening_message"),
            metadata.get("opening_line"),
            metadata.get("initial_message"),
            metadata.get("first_message"),
            metadata.get("start_message"),
        )

        if row.get("ai_role"):
            metadata["ai_role"] = row["ai_role"]
        if row.get("user_role"):
            metadata["user_role"] = row["user_role"]

        bind.execute(
            scenarios.update()
            .where(scenarios.c.id == row["id"])
            .values(
                metadata=metadata,
                opening_message=opening_message or None,
            )
        )

    inspector = sa.inspect(bind)
    with op.batch_alter_table("scenarios") as batch_op:
        if _has_column(inspector, "scenarios", "user_role"):
            batch_op.drop_column("user_role")
        if _has_column(inspector, "scenarios", "ai_role"):
            batch_op.drop_column("ai_role")

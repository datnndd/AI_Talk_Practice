#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path


BOOLEAN_COLUMNS: dict[str, tuple[str, ...]] = {
    "scenarios": ("is_active", "is_pre_generated"),
    "scenario_variations": ("is_active", "is_pregenerated", "is_approved"),
}

TRUTHY = {"true", "1", "t", "yes", "y", "on"}
FALSY = {"false", "0", "f", "no", "n", "off"}


def normalize_column(connection: sqlite3.Connection, table: str, column: str) -> int:
    cursor = connection.cursor()
    rows = cursor.execute(f"SELECT rowid, {column} FROM {table}").fetchall()
    updated = 0

    for rowid, raw_value in rows:
        normalized = None

        if isinstance(raw_value, str):
            lowered = raw_value.strip().lower()
            if lowered in TRUTHY:
                normalized = 1
            elif lowered in FALSY:
                normalized = 0
        elif raw_value is True:
            normalized = 1
        elif raw_value is False:
            normalized = 0

        if normalized is None or raw_value == normalized:
            continue

        cursor.execute(f"UPDATE {table} SET {column} = ? WHERE rowid = ?", (normalized, rowid))
        updated += 1

    return updated


def backup_database(path: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = path.with_suffix(f"{path.suffix}.bak-{timestamp}")
    shutil.copy2(path, backup_path)
    return backup_path


def main() -> int:
    db_path = Path("backend/ai_talk_practice.db")

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return 1

    backup_path = backup_database(db_path)
    print(f"Backup created: {backup_path}")

    connection = sqlite3.connect(db_path)
    total_updates = 0

    try:
        for table, columns in BOOLEAN_COLUMNS.items():
            exists = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name = ?",
                (table,),
            ).fetchone()
            if not exists:
                continue

            for column in columns:
                updated = normalize_column(connection, table, column)
                total_updates += updated
                print(f"{table}.{column}: updated {updated} rows")

        connection.commit()
    finally:
        connection.close()

    print(f"Normalization complete. Total updated rows: {total_updates}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

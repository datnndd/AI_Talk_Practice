import os
import sqlite3


NEEDED_SCENARIO_COLUMNS = {
    "ai_role": "VARCHAR(500) DEFAULT '' NOT NULL",
    "user_role": "VARCHAR(500) DEFAULT '' NOT NULL",
    "time_limit_minutes": "INTEGER",
}

def repair():
    db_path = 'ai_talk_practice.db'
    if not os.path.exists(db_path):
        print(f"Error: {db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check current columns
        cursor.execute("PRAGMA table_info(scenarios)")
        columns = [col[1] for col in cursor.fetchall()]
        
        for col_name, col_type in NEEDED_SCENARIO_COLUMNS.items():
            if col_name not in columns:
                print(f"Adding column {col_name}...")
                cursor.execute(f"ALTER TABLE scenarios ADD COLUMN {col_name} {col_type}")
                print(f"Column {col_name} added successfully.")
            else:
                print(f"Column {col_name} already exists.")
        
        conn.commit()
        conn.close()
        print("Database repair complete.")
        
    except Exception as e:
        print(f"Error during repair: {e}")

if __name__ == "__main__":
    repair()

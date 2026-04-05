import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'ai_talk_practice.db')

def fix_database():
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    print("Connecting to database...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if is_pre_generated exists
        cursor.execute("SELECT is_pre_generated FROM scenarios LIMIT 1")
    except sqlite3.OperationalError:
        print("Column 'is_pre_generated' is missing. Adding it...")
        cursor.execute("ALTER TABLE scenarios ADD COLUMN is_pre_generated BOOLEAN NOT NULL DEFAULT 0;")

    try:
        # Check if pre_gen_count exists
        cursor.execute("SELECT pre_gen_count FROM scenarios LIMIT 1")
    except sqlite3.OperationalError:
        print("Column 'pre_gen_count' is missing. Adding it...")
        cursor.execute("ALTER TABLE scenarios ADD COLUMN pre_gen_count INTEGER NOT NULL DEFAULT 8;")

    conn.commit()
    conn.close()
    print("Database schema successfully updated!")

if __name__ == '__main__':
    fix_database()

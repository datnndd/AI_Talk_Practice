import sqlite3

def check_schema():
    try:
        conn = sqlite3.connect('ai_talk_practice.db')
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(scenarios)")
        columns = cursor.fetchall()
        print("Columns in 'scenarios' table:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_schema()

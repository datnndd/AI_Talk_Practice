import sqlite3
import os

def export_schema():
    db_path = 'ai_talk_practice.db'
    output_path = 'current_schema.txt'
    
    if not os.path.exists(db_path):
        with open(output_path, 'w') as f:
            f.write(f"Error: {db_path} not found in {os.getcwd()}")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        with open(output_path, 'w') as f:
            for table in tables:
                table_name = table[0]
                f.write(f"\nTable: {table_name}\n")
                f.write("-" * 20 + "\n")
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                for col in columns:
                    f.write(f"  - {col[1]} ({col[2]})\n")
        
        conn.close()
    except Exception as e:
        with open(output_path, 'w') as f:
            f.write(f"Error: {e}")

if __name__ == "__main__":
    export_schema()

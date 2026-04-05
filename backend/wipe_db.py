import os
import sqlite3

db_path = os.path.join(os.path.dirname(__file__), 'ai_talk_practice.db')

def wipe_and_seed():
    # 1. Back up and remove the old database
    if os.path.exists(db_path):
        backup_path = db_path + '.bak'
        if os.path.exists(backup_path):
            os.remove(backup_path)
        os.rename(db_path, backup_path)
        print(f"Old database backed up to {backup_path}")
    else:
        print("No database found to wipe.")

    # 2. Tell the user to run backend / seed
    print("\nDatabase wiped successfully!")
    print("Now, please follow these steps to recreate it with the PERFECT schema:\n")
    print("1. Restart your backend (this auto-creates the new DB schema):")
    print("   bash run.sh")
    print("\n2. In ANOTHER terminal window, run the seed script to recreate your admin user:")
    print("   cd /home/datnd/Projects/AI_Talk_Practice/backend")
    print("   source venv/bin/activate")
    print("   python -m app.seed")

if __name__ == '__main__':
    wipe_and_seed()

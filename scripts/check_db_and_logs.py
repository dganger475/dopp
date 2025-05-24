import os
import sqlite3
import sys

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'faces.db'))
LOGS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'logs'))
APP_LOG = os.path.join(LOGS_DIR, 'app.log')


def check_db_schema():
    print(f"Checking database at: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("[ERROR] Database file does not exist.")
        return False
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(user_matches);")
    columns = cursor.fetchall()
    print("user_matches columns:")
    for col in columns:
        print(f"  - {col[1]}")
    conn.close()
    return True

def cleanup_logs():
    print(f"Checking logs directory at: {LOGS_DIR}")
    if not os.path.exists(LOGS_DIR):
        print("[INFO] Logs directory does not exist. Skipping log cleanup.")
        return
    for fname in os.listdir(LOGS_DIR):
        if fname.startswith('app.log'):
            fpath = os.path.join(LOGS_DIR, fname)
            try:
                os.remove(fpath)
                print(f"[INFO] Deleted {fpath}")
            except Exception as e:
                print(f"[WARNING] Could not delete {fpath}: {e}")

def main():
    print("--- DB SCHEMA CHECK ---")
    db_ok = check_db_schema()
    print("\n--- LOG CLEANUP ---")
    cleanup_logs()
    if db_ok:
        print("\n[INFO] DB schema and logs cleaned up. Please restart your Flask app.")
    else:
        print("\n[WARNING] DB schema issue detected. Please check your DB path and try again.")

if __name__ == "__main__":
    main()

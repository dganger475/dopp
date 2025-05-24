import os
import sqlite3


def print_table_schema(db_path, table_name):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    print(f"\nSchema for table '{table_name}':")
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        if columns:
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
        else:
            print("  Table does not exist.")
    except Exception as e:
        print(f"  Error: {e}")
    finally:
        conn.close()

def main():
    db_files = [
        'faces.db',
        'users.db',
    ]
    table_names = [
        'user_matches',
        'users',
        'faces',
    ]
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for db_file in db_files:
        db_path = os.path.join(base_dir, db_file)
        if os.path.exists(db_path):
            print(f"\n--- Checking {db_file} ---")
            for table in table_names:
                print_table_schema(db_path, table)
        else:
            print(f"\nDatabase file not found: {db_path}")

if __name__ == "__main__":
    main()

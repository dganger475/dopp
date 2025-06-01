import sqlite3
import os
import sys

def check_database_schema():
    db_path = 'faces.db'
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        print('Tables in database:')
        for table in tables:
            print(f"\nTable: {table[0]}")
            cursor.execute(f"PRAGMA table_info({table[0]})")
            columns = cursor.fetchall()
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    try:
        check_database_schema()
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1) 
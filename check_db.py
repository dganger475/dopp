import sqlite3
import sys

def check_db():
    try:
        # Connect to the database
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table[0]}")
        
        # Check likes table
        print("\nChecking 'likes' table:")
        try:
            cursor.execute("PRAGMA table_info(likes)")
            columns = cursor.fetchall()
            if columns:
                print("Columns in 'likes' table:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("  - 'likes' table does not exist or has no columns")
        except sqlite3.Error as e:
            print(f"  - Error checking 'likes' table: {e}")
        
        # Check comments table
        print("\nChecking 'comments' table:")
        try:
            cursor.execute("PRAGMA table_info(comments)")
            columns = cursor.fetchall()
            if columns:
                print("Columns in 'comments' table:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("  - 'comments' table does not exist or has no columns")
        except sqlite3.Error as e:
            print(f"  - Error checking 'comments' table: {e}")
        
        # Check posts table
        print("\nChecking 'posts' table:")
        try:
            cursor.execute("PRAGMA table_info(posts)")
            columns = cursor.fetchall()
            if columns:
                print("Columns in 'posts' table:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            else:
                print("  - 'posts' table does not exist or has no columns")
        except sqlite3.Error as e:
            print(f"  - Error checking 'posts' table: {e}")
        
    except sqlite3.Error as e:
        print(f"Database error: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_db()

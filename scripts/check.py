import sqlite3

db_path = 'faces.db'  # Change this if your database is in a different folder

def check_schema(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("\n📄 Tables in the database:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    for table_name in cursor.fetchall():
        print(f"- {table_name[0]}")

    print("\n🔍 Schema of each table:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()

    for table_name in tables:
        print(f"\n➡️ Schema for table: {table_name[0]}")
        cursor.execute(f"PRAGMA table_info({table_name[0]});")
        for column in cursor.fetchall():
            print(column)

    conn.close()

check_schema(db_path)

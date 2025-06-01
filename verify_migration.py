import os
import sqlite3
import psycopg2
from dotenv import load_dotenv
from tabulate import tabulate

# Load environment variables
load_dotenv()

def get_sqlite_connection():
    """Connect to SQLite database."""
    return sqlite3.connect('faces.db')

def get_postgres_connection():
    """Connect to PostgreSQL database."""
    return psycopg2.connect(os.getenv('DATABASE_URL'))

def get_table_counts(conn, table_name):
    """Get row count for a table."""
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]

def verify_migration():
    """Verify the migration by comparing table counts and data integrity."""
    print("Starting migration verification...")
    
    # Connect to both databases
    sqlite_conn = get_sqlite_connection()
    pg_conn = get_postgres_connection()
    
    try:
        # Get all tables from SQLite
        sqlite_cursor = sqlite_conn.cursor()
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [table[0] for table in sqlite_cursor.fetchall() if table[0] != 'sqlite_sequence']
        
        # Compare table counts
        results = []
        for table in tables:
            try:
                sqlite_count = get_table_counts(sqlite_conn, table)
                pg_count = get_table_counts(pg_conn, table)
                status = "✅" if sqlite_count == pg_count else "❌"
                results.append([table, sqlite_count, pg_count, status])
            except Exception as e:
                results.append([table, "Error", "Error", f"❌ ({str(e)})"])
        
        # Print results
        print("\nMigration Verification Results:")
        print(tabulate(results, 
                      headers=["Table", "SQLite Count", "PostgreSQL Count", "Status"],
                      tablefmt="grid"))
        
        # Check for any mismatches
        mismatches = [r for r in results if r[3] != "✅"]
        if mismatches:
            print("\n⚠️  Warnings:")
            for mismatch in mismatches:
                print(f"- {mismatch[0]}: Count mismatch or error")
        else:
            print("\n✅ All tables verified successfully!")
            
    finally:
        sqlite_conn.close()
        pg_conn.close()

if __name__ == "__main__":
    verify_migration() 
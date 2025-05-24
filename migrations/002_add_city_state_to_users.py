"""
Migration to add city and state columns to users table
"""
import sqlite3

def migrate(app):
    """Add city and state columns to users table"""
    db_path = app.config.get("DB_PATH", "faces.db")
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add city column if it doesn't exist
        if 'city' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN city TEXT")
        
        # Add state column if it doesn't exist
        if 'state' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN state TEXT")
        
        conn.commit()
    
    return True 
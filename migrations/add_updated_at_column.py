import sqlite3
import os

def add_updated_at_column():
    """Add updated_at column to posts table if it doesn't exist."""
    db_path = os.path.join('instance', 'users.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(posts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'updated_at' not in columns:
            print("Adding updated_at column to posts table...")
            cursor.execute("ALTER TABLE posts ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            cursor.execute("UPDATE posts SET updated_at = created_at WHERE updated_at IS NULL")
            conn.commit()
            print("Column added successfully!")
        else:
            print("updated_at column already exists")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    add_updated_at_column() 
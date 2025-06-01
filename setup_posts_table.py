import sqlite3
import os
import sys

def setup_posts_table():
    db_path = os.path.join('instance', 'users.db')
    
    if not os.path.exists(db_path):
        print(f"Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create posts table with all required columns
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_match_post INTEGER DEFAULT 0,
            face_filename TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Create indexes for better performance
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at)")
        
        conn.commit()
        print("Posts table created successfully!")
        return True
            
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    try:
        success = setup_posts_table()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1) 
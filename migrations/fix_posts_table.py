import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_posts_table():
    """Fix the posts table structure with all required columns."""
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Create a new table with the correct structure
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS posts_new (
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
        
        # Copy data from old table if it exists
        cursor.execute("PRAGMA table_info(posts)")
        old_columns = [col[1] for col in cursor.fetchall()]
        
        if old_columns:
            # Get the data from the old table
            cursor.execute("SELECT * FROM posts")
            old_data = cursor.fetchall()
            
            # Insert data into new table
            for row in old_data:
                cursor.execute("""
                INSERT INTO posts_new (user_id, content, created_at, updated_at, is_match_post, face_filename)
                VALUES (?, ?, ?, ?, ?, ?)
                """, row)
            
            # Drop the old table
            cursor.execute("DROP TABLE posts")
        
        # Rename new table to posts
        cursor.execute("ALTER TABLE posts_new RENAME TO posts")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_user_id ON posts(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_posts_created_at ON posts(created_at)")
        
        conn.commit()
        logger.info("Posts table structure fixed successfully!")
        return True
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    fix_posts_table() 
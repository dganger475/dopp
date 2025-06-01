import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_posts_table():
    """Recreate the posts table with all required columns."""
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Drop the existing table
        cursor.execute("DROP TABLE IF EXISTS posts")
        
        # Create the table with the correct structure
        cursor.execute("""
        CREATE TABLE posts (
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
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_posts_user_id ON posts(user_id)")
        cursor.execute("CREATE INDEX idx_posts_created_at ON posts(created_at)")
        
        conn.commit()
        logger.info("Posts table recreated successfully!")
        return True
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    recreate_posts_table() 
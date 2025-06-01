import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_likes_table():
    """Create the likes table with all required columns."""
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Create the table with the correct structure
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            post_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (post_id) REFERENCES posts(id),
            UNIQUE(user_id, post_id)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_user_id ON likes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_likes_post_id ON likes(post_id)")
        
        conn.commit()
        logger.info("Likes table created successfully!")
        return True
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    create_likes_table() 
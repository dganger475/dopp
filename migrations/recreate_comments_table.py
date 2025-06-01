import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_comments_table():
    """Recreate the comments table with all required columns."""
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Drop the existing table
        cursor.execute("DROP TABLE IF EXISTS comments")
        
        # Create the table with the correct structure
        cursor.execute("""
        CREATE TABLE comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (post_id) REFERENCES posts(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX idx_comments_post_id ON comments(post_id)")
        cursor.execute("CREATE INDEX idx_comments_user_id ON comments(user_id)")
        
        conn.commit()
        logger.info("Comments table recreated successfully!")
        return True
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    recreate_comments_table() 
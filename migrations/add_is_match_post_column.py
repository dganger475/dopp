import sqlite3
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_is_match_post_column():
    """Add is_match_post column to posts table if it doesn't exist."""
    db_path = 'faces.db'
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(posts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'is_match_post' not in columns:
            logger.info("Adding is_match_post column to posts table...")
            cursor.execute("ALTER TABLE posts ADD COLUMN is_match_post INTEGER DEFAULT 0")
            conn.commit()
            logger.info("Column added successfully!")
        else:
            logger.info("is_match_post column already exists")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    return True

if __name__ == '__main__':
    add_is_match_post_column() 
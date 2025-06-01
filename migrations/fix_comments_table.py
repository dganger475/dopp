import sqlite3
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_comments_table():
    """Fix the comments table structure by adding the missing updated_at column."""
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(comments)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'updated_at' not in columns:
            logger.info("Adding updated_at column to comments table...")
            cursor.execute("ALTER TABLE comments ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            cursor.execute("UPDATE comments SET updated_at = created_at WHERE updated_at IS NULL")
            conn.commit()
            logger.info("Column added successfully!")
        else:
            logger.info("updated_at column already exists")
            
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    return True

if __name__ == '__main__':
    fix_comments_table() 
import sqlite3
import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_updated_at_column():
    """Add updated_at column to posts table if it doesn't exist."""
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("PRAGMA table_info(posts)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'updated_at' not in columns:
            logger.info("Adding updated_at column to posts table...")
            cursor.execute("ALTER TABLE posts ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            cursor.execute("UPDATE posts SET updated_at = created_at WHERE updated_at IS NULL")
            conn.commit()
            logger.info("Column added successfully!")
        else:
            logger.info("updated_at column already exists")
            
    except sqlite3.Error as e:
        logger.error(f"SQLite error: {e}")
        return False
    except Exception as e:
        logger.error(f"Error: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()
    return True

if __name__ == '__main__':
    success = add_updated_at_column()
    sys.exit(0 if success else 1) 
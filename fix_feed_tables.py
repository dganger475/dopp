import sqlite3
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_db_path():
    """Get the path to the SQLite database file."""
    # Assuming the database is in the same directory as this script
    db_path = Path(__file__).parent / 'faces.db'
    return str(db_path)

def run_fix():
    """Fix the feed-related tables in the database."""
    db_path = get_db_path()
    logger.info(f"Connecting to database at: {db_path}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Check if likes table exists and has the correct schema
        cursor.execute("PRAGMA table_info(likes)")
        like_columns = [col[1] for col in cursor.fetchall()]
        
        if not like_columns:
            # Create likes table if it doesn't exist
            logger.info("Creating likes table...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(post_id, user_id)
            )
            """)
            logger.info("Created likes table")
        else:
            # Ensure all required columns exist
            required_columns = ['id', 'post_id', 'user_id', 'created_at']
            for col in required_columns:
                if col not in like_columns:
                    if col == 'created_at':
                        cursor.execute("ALTER TABLE likes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                        logger.info("Added created_at column to likes table")
        
        # 2. Check if comments table exists and has the correct schema
        cursor.execute("PRAGMA table_info(comments)")
        comment_columns = [col[1] for col in cursor.fetchall()]
        
        if not comment_columns:
            # Create comments table if it doesn't exist
            logger.info("Creating comments table...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                parent_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE
            )
            """)
            logger.info("Created comments table")
        else:
            # Ensure parent_id column exists
            if 'parent_id' not in comment_columns:
                try:
                    cursor.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE")
                    logger.info("Added parent_id column to comments table")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" not in str(e):
                        raise
                    logger.info("parent_id column already exists in comments table")
        
        # 3. Create a view or function to implement Like.get_by_user_and_post
        # This is a workaround since SQLite doesn't support stored functions like PostgreSQL
        # The application code will need to query this view
        cursor.execute("""
        CREATE VIEW IF NOT EXISTS user_post_likes AS
        SELECT id, post_id, user_id, created_at
        FROM likes
        WHERE post_id = :post_id AND user_id = :user_id
        LIMIT 1;
        """)
        
        conn.commit()
        logger.info("Feed tables fixed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error fixing feed tables: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if run_fix():
        logger.info("Database fix completed successfully")
    else:
        logger.error("Database fix failed")

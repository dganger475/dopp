import sqlite3
import logging
from utils.db.database import get_users_db_connection

def run_migration():
    """Add or update feed-related tables (likes, comments) for social feed functionality."""
    conn = get_users_db_connection()
    if not conn:
        logging.error("Failed to connect to database")
        return False
    
    try:
        cursor = conn.cursor()
        
        # Check if likes table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='likes'")
        if not cursor.fetchone():
            # Create likes table
            cursor.execute("""
            CREATE TABLE likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                UNIQUE(post_id, user_id)
            )
            """)
            logging.info("Created likes table")
        else:
            # Ensure likes table has all required columns
            try:
                cursor.execute("ALTER TABLE likes ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                logging.info("Added created_at column to likes table")
            except sqlite3.OperationalError:
                # Column already exists
                pass
        
        # Check if comments table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='comments'")
        if not cursor.fetchone():
            # Create comments table
            cursor.execute("""
            CREATE TABLE comments (
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
            logging.info("Created comments table")
        else:
            # Ensure comments table has all required columns
            try:
                cursor.execute("ALTER TABLE comments ADD COLUMN parent_id INTEGER REFERENCES comments(id) ON DELETE CASCADE")
                logging.info("Added parent_id column to comments table")
            except sqlite3.OperationalError:
                # Column already exists
                pass
        
        conn.commit()
        logging.info("Feed tables migration completed successfully")
        return True
    
    except Exception as e:
        logging.error(f"Error in feed tables migration: {e}")
        conn.rollback()
        return False
    
    finally:
        conn.close()

if __name__ == "__main__":
    run_migration()

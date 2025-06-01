import sqlite3
import logging
import sys
import traceback
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_users_db_connection(db_path='faces.db'):
    """Connect to the users database."""
    try:
        logger.info(f"Connecting to database: {db_path}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def debug_get_by_post_and_user(post_id, user_id):
    """Debug the get_by_post_and_user method in the Like class."""
    conn = get_users_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return None

    try:
        logger.info(f"Querying likes table for post_id={post_id} and user_id={user_id}")
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM likes WHERE post_id = ? AND user_id = ?",
            (post_id, user_id),
        )
        like_data = cursor.fetchone()

        if like_data:
            logger.info(f"Found like: {dict(like_data)}")
            return dict(like_data)
        
        logger.info("No like found")
        return None

    except Exception as e:
        logger.error(f"Error in debug_get_by_post_and_user: {e}")
        logger.error(traceback.format_exc())
        return None
    finally:
        conn.close()

def debug_like_delete(post_id, user_id):
    """Debug the delete method in the Like class."""
    conn = get_users_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False

    try:
        logger.info(f"Attempting to delete like for post_id={post_id} and user_id={user_id}")
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM likes WHERE post_id = ? AND user_id = ?",
            (post_id, user_id),
        )

        rows_affected = cursor.rowcount
        logger.info(f"Rows affected by delete: {rows_affected}")

        conn.commit()
        logger.info("Delete operation committed")
        return True

    except Exception as e:
        logger.error(f"Error in debug_like_delete: {e}")
        logger.error(traceback.format_exc())
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()

def debug_like_create(post_id, user_id):
    """Debug the create method in the Like class."""
    conn = get_users_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return None

    try:
        logger.info(f"Checking if like already exists for post_id={post_id} and user_id={user_id}")
        existing_like = debug_get_by_post_and_user(post_id, user_id)
        if existing_like:
            logger.info("Like already exists, returning existing like")
            return existing_like

        logger.info(f"Creating new like for post_id={post_id} and user_id={user_id}")
        cursor = conn.cursor()
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        cursor.execute(
            "INSERT INTO likes (post_id, user_id, created_at) VALUES (?, ?, ?)", 
            (post_id, user_id, created_at)
        )

        conn.commit()
        logger.info(f"New like created with ID: {cursor.lastrowid}")

        # Get the newly created like
        cursor.execute("SELECT * FROM likes WHERE id = ?", (cursor.lastrowid,))
        new_like = cursor.fetchone()
        
        if new_like:
            logger.info(f"Retrieved new like: {dict(new_like)}")
            return dict(new_like)
        
        logger.warning("Failed to retrieve newly created like")
        return None

    except Exception as e:
        logger.error(f"Error in debug_like_create: {e}")
        logger.error(traceback.format_exc())
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()

def check_post_exists(post_id):
    """Check if a post exists in the database."""
    conn = get_users_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return False

    try:
        logger.info(f"Checking if post with ID={post_id} exists")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM posts WHERE id = ?", (post_id,))
        post = cursor.fetchone()
        
        if post:
            logger.info(f"Post found: {post['id']}")
            return True
        
        logger.warning(f"Post with ID={post_id} does not exist")
        return False

    except Exception as e:
        logger.error(f"Error in check_post_exists: {e}")
        logger.error(traceback.format_exc())
        return False
    finally:
        conn.close()

def simulate_like_endpoint(post_id, user_id):
    """Simulate the like/unlike endpoint with detailed logging."""
    logger.info(f"=== Starting simulation for post_id={post_id}, user_id={user_id} ===")
    
    # Check if post exists
    if not check_post_exists(post_id):
        logger.error("Post not found")
        return {"success": False, "error": "Post not found"}

    try:
        # Check if user has already liked the post
        logger.info("Checking if user has already liked the post")
        existing_like = debug_get_by_post_and_user(post_id, user_id)
        
        if existing_like:
            # Unlike the post
            logger.info("User has already liked the post, removing like")
            if debug_like_delete(post_id, user_id):
                logger.info("Like successfully removed")
                return {"success": True, "action": "unliked"}
            else:
                logger.error("Failed to remove like")
                return {"success": False, "error": "Failed to remove like"}
        else:
            # Like the post
            logger.info("User has not liked the post, adding like")
            new_like = debug_like_create(post_id, user_id)
            if new_like:
                logger.info("Like successfully added")
                return {"success": True, "action": "liked"}
            else:
                logger.error("Failed to add like")
                return {"success": False, "error": "Failed to add like"}

    except Exception as e:
        logger.error(f"Error in simulate_like_endpoint: {e}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": f"Failed to process like: {str(e)}"}

def debug_database_schema():
    """Check the database schema for the likes table."""
    conn = get_users_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return

    try:
        logger.info("Checking database schema for likes table")
        cursor = conn.cursor()
        
        # Check if likes table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='likes'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            logger.error("Likes table does not exist in the database")
            return
        
        logger.info("Likes table exists")
        
        # Get schema of likes table
        cursor.execute("PRAGMA table_info(likes)")
        columns = cursor.fetchall()
        
        logger.info("Likes table schema:")
        for col in columns:
            logger.info(f"  Column: {col['name']}, Type: {col['type']}, NotNull: {col['notnull']}, Default: {col['dflt_value']}, PK: {col['pk']}")
        
        # Check sample data
        cursor.execute("SELECT COUNT(*) as count FROM likes")
        count = cursor.fetchone()['count']
        logger.info(f"Total likes in database: {count}")
        
        if count > 0:
            cursor.execute("SELECT * FROM likes LIMIT 5")
            sample_likes = cursor.fetchall()
            logger.info("Sample likes:")
            for like in sample_likes:
                logger.info(f"  {dict(like)}")

    except Exception as e:
        logger.error(f"Error in debug_database_schema: {e}")
        logger.error(traceback.format_exc())
    finally:
        conn.close()

if __name__ == "__main__":
    # Default values
    post_id = 1
    user_id = 1
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        post_id = int(sys.argv[1])
    if len(sys.argv) > 2:
        user_id = int(sys.argv[2])
    
    logger.info("=== Starting debug script ===")
    logger.info(f"Using post_id={post_id}, user_id={user_id}")
    
    # Debug the database schema
    debug_database_schema()
    
    # Simulate the endpoint
    result = simulate_like_endpoint(post_id, user_id)
    logger.info(f"Result: {result}")
    
    logger.info("=== Debug script completed ===")

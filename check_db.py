import sqlite3
import os
import logging
from werkzeug.security import check_password_hash

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Check database connection and user data."""
    # Get database path
    db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces.db')
    logger.info(f"Checking database at: {db_path}")
    
    if not os.path.exists(db_path):
        logger.error(f"Database file not found at {db_path}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            logger.error("Users table does not exist")
            return False
            
        # Get all users
        cursor.execute("SELECT id, username, email, password_hash FROM users")
        users = cursor.fetchall()
        
        if not users:
            logger.info("No users found in database")
            return False
            
        logger.info(f"Found {len(users)} users in database:")
        for user in users:
            logger.info(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
            
        # Check specific user
        test_email = "officialrealkeed@gmail.com"
        cursor.execute("SELECT * FROM users WHERE email = ?", (test_email,))
        user = cursor.fetchone()
        
        if user:
            logger.info(f"Found user with email {test_email}:")
            logger.info(f"ID: {user[0]}, Username: {user[1]}, Email: {user[2]}")
        else:
            logger.info(f"No user found with email {test_email}")
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking database: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_database()

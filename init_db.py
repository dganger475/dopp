import os
import sys
import logging
from utils.db.database import setup_users_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database with all required tables."""
    try:
        # Ensure instance directory exists
        os.makedirs('instance', exist_ok=True)
        
        # Initialize database tables
        success = setup_users_db()
        if success:
            logger.info("Database initialized successfully!")
            return True
        else:
            logger.error("Failed to initialize database")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1) 
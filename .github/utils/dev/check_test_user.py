"""
Development Utility - Check User
====================================

Checks if a specific user exists in the database and verifies its credentials.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from app import create_app
from models.user import User
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_user(username="realkeed"):
    """Check if user exists and verify its details."""
    try:
        # Create Flask app and context
        app = create_app()
        with app.app_context():
            # Get user from database
            user = User.get_by_username(username)
            if not user:
                logger.error(f"User '{username}' not found in database")
                return False
                
            logger.info(f"Found user:")
            logger.info(f"Username: {user.username}")
            logger.info(f"Email: {user.email}")
            logger.info(f"Password hash: {user.password_hash}")
            return True
                
    except Exception as e:
        logger.error(f"Error checking user: {str(e)}")
        return False

if __name__ == "__main__":
    # Check the user
    success = check_user()
    if success:
        print("\nUser found successfully!")
    else:
        print("\nFailed to find user") 
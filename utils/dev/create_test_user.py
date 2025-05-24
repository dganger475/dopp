"""
Development Utility - Create Test User
====================================

Creates a test user for development purposes.
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
from utils.db.database import get_users_db_connection
import logging

logger = logging.getLogger(__name__)

def create_test_user(username="testuser", password="testpass123", email="test@example.com"):
    """Create a test user for development."""
    try:
        # Check if user already exists
        existing_user = User.get_by_username(username)
        if existing_user:
            logger.info(f"Test user '{username}' already exists")
            return existing_user
            
        # Create new test user
        user = User.create(
            username=username,
            email=email,
            password=password,
            first_name="Test",
            last_name="User",
            bio="This is a test user account",
            hometown="Test City",
            current_location_city="Test City",
            current_location_state="TS",
            profile_visibility="public"
        )
        
        if user:
            logger.info(f"Created test user: {username}")
            logger.info(f"Password: {password}")
            return user
        else:
            logger.error("Failed to create test user")
            return None
            
    except Exception as e:
        logger.error(f"Error creating test user: {str(e)}")
        return None

if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Create Flask app and context
    app = create_app()
    with app.app_context():
        # Create the test user
        user = create_test_user()
        if user:
            print(f"\nTest user created successfully!")
            print(f"Username: {user.username}")
            print(f"Password: testpass123")
            print(f"Email: {user.email}")
        else:
            print("Failed to create test user") 
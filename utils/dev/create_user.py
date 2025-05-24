"""
Development Utility - Create User
====================================

Creates a new user in the database.
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

def create_user(username, password, email):
    """Create a new user."""
    try:
        # Create Flask app and context
        app = create_app()
        with app.app_context():
            # Check if user already exists
            existing_user = User.get_by_username(username)
            if existing_user:
                logger.info(f"User '{username}' already exists")
                return existing_user
                
            # Create new user
            user = User.create(
                username=username,
                email=email,
                password=password,
                first_name="",
                last_name="",
                bio="",
                hometown="",
                current_location_city="",
                current_location_state="",
                profile_visibility="public"
            )
            
            if user:
                logger.info(f"Created user: {username}")
                logger.info(f"Password: {password}")
                return user
            else:
                logger.error("Failed to create user")
                return None
                
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        return None

if __name__ == "__main__":
    # Create the user
    user = create_user(
        username="realkeed",
        password="your_password_here",  # Replace with actual password
        email="realkeed@example.com"    # Replace with actual email
    )
    if user:
        print("\nUser created successfully!")
    else:
        print("\nFailed to create user") 
#!/usr/bin/env python
"""
Initialize database migrations.
This script creates the initial migration for the database schema.
"""

import logging
import os
import sys

from dotenv import load_dotenv
from flask_migrate import init, migrate, upgrade

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables
load_dotenv()

# Import the Flask application
from app import app, db

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def init_migrations():
    """Initialize database migrations."""
    try:
        with app.app_context():
            # Check if migrations directory exists
            migrations_dir = os.path.join(app.root_path, 'migrations')
            if not os.path.exists(os.path.join(migrations_dir, 'env.py')):
                logger.info("Initializing migrations directory...")
                os.system(f"flask db init")
            
            # Create initial migration
            logger.info("Creating initial migration...")
            os.system(f"flask db migrate -m \"Initial migration\"")
            
            # Apply migration
            logger.info("Applying migration...")
            os.system(f"flask db upgrade")
            
            logger.info("Database migrations initialized successfully!")
            return True
    except Exception as e:
        logger.error(f"Error initializing migrations: {e}")
        return False

if __name__ == "__main__":
    init_migrations()

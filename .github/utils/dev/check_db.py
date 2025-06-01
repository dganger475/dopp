"""
Development Utility - Check Database
====================================

Checks the contents of faces.db.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_db():
    """Check the contents of faces.db."""
    try:
        # Connect to the database
        db_path = os.path.join(PROJECT_ROOT, 'faces.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        logger.info("Tables in database:")
        for table in tables:
            logger.info(f"- {table[0]}")
            
        # Check users table
        cursor.execute("SELECT * FROM users WHERE username = 'realkeed';")
        user = cursor.fetchone()
        if user:
            logger.info("\nFound user 'realkeed':")
            cursor.execute("PRAGMA table_info(users);")
            columns = [col[1] for col in cursor.fetchall()]
            for i, col in enumerate(columns):
                logger.info(f"{col}: {user[i]}")
        else:
            logger.info("\nUser 'realkeed' not found")
            
    except Exception as e:
        logger.error(f"Error checking database: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_db() 
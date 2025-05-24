"""
Development Utility - Fix User Data
====================================

Fixes corrupted user data in faces.db.
"""

import os
import sys
import sqlite3
from pathlib import Path

# Add project root to Python path
PROJECT_ROOT = str(Path(__file__).parent.parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from werkzeug.security import generate_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_user():
    """Fix corrupted user data."""
    try:
        # Connect to the database
        db_path = os.path.join(PROJECT_ROOT, 'faces.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Fix the user data
        cursor.execute("""
            UPDATE users 
            SET 
                first_name = 'ReaL',
                password_hash = ?
            WHERE username = 'realkeed';
        """, (generate_password_hash('Adidas11@'),))
        
        conn.commit()
        logger.info("User data fixed successfully")
            
    except Exception as e:
        logger.error(f"Error fixing user data: {str(e)}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_user()
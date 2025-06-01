"""
Script to check user authentication details in the database.
"""

import os
import sys
from pathlib import Path
import sqlite3
from werkzeug.security import check_password_hash

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

def check_user_auth(email="newguy@gmail.com", password="Test123!"):
    """Check user authentication details."""
    try:
        # Connect to the database
        db_path = os.path.join(PROJECT_ROOT, 'faces.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get user details
        cursor.execute("""
            SELECT id, username, email, password_hash 
            FROM users 
            WHERE email = ?
        """, (email,))
        
        user = cursor.fetchone()
        if not user:
            print(f"User with email {email} not found")
            return False
            
        print(f"\nUser found:")
        print(f"ID: {user[0]}")
        print(f"Username: {user[1]}")
        print(f"Email: {user[2]}")
        print(f"Password hash exists: {bool(user[3])}")
        
        # Check password
        if user[3]:
            is_valid = check_password_hash(user[3], password)
            print(f"Password is valid: {is_valid}")
            return is_valid
        else:
            print("No password hash found")
            return False
            
    except Exception as e:
        print(f"Error checking user auth: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_user_auth() 
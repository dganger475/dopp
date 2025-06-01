"""
Script to update a user's password in the database.
"""

import os
import sys
from pathlib import Path
import sqlite3
from werkzeug.security import generate_password_hash

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

def update_user_password(email="newguy@gmail.com", new_password="Test123!"):
    """Update user's password."""
    try:
        # Connect to the database
        db_path = os.path.join(PROJECT_ROOT, 'faces.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Generate new password hash
        password_hash = generate_password_hash(new_password)
        
        # Update user's password
        cursor.execute("""
            UPDATE users 
            SET password_hash = ? 
            WHERE email = ?
        """, (password_hash, email))
        
        if cursor.rowcount > 0:
            conn.commit()
            print(f"Password updated for user {email}")
            return True
        else:
            print(f"User {email} not found")
            return False
            
    except Exception as e:
        print(f"Error updating password: {str(e)}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    update_user_password() 
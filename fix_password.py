import os
import sys
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

# Configure paths
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces.db')

def fix_password(email="officialrealkeed@gmail.com", new_password="Adidas11@"):
    """Fix user's password."""
    print(f"Fixing password for {email}")
    
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return False
    
    try:
        # Connect to database
        conn = sqlite3.connect(DB_PATH)
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
            print(f"Password updated for {email}")
            return True
        else:
            print(f"User {email} not found")
            return False
            
    except Exception as e:
        print(f"Error updating password: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_password() 
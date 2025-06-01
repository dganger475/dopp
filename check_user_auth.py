import sqlite3
import os
import sys
from werkzeug.security import check_password_hash

# Configure paths
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'faces.db')

def check_user_exists():
    """Check if users exist in the database and print their details"""
    print(f"Checking database at: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"Database file not found at {DB_PATH}")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Check if users table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            print("The 'users' table does not exist in the database")
            return
        
        # Get all users
        cursor.execute("SELECT * FROM users LIMIT 10")
        columns = [description[0] for description in cursor.description]
        users = cursor.fetchall()
        
        if not users:
            print("No users found in the database")
            return
        
        print(f"Found {len(users)} users in the database")
        print("\nUser columns:", columns)
        
        # Print usernames and emails for all users
        print("\nUsers:")
        username_index = columns.index('username') if 'username' in columns else None
        email_index = columns.index('email') if 'email' in columns else None
        password_index = columns.index('password_hash') if 'password_hash' in columns else None
        id_index = columns.index('id') if 'id' in columns else None
        
        for user in users:
            print("\nUser ID:", user[id_index] if id_index is not None else "Unknown")
            print("Username:", user[username_index] if username_index is not None else "Unknown")
            print("Email:", user[email_index] if email_index is not None else "Unknown")
            print("Password hash exists:", bool(user[password_index]) if password_index is not None else "Unknown")
    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

def test_login(username, password):
    """Test if a username/password combination would work"""
    print(f"\nTesting login for username: {username}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Try to find user by username
        cursor.execute("SELECT id, username, password_hash FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        
        if not user:
            print(f"No user found with username: {username}")
            
            # Try to find by email instead
            cursor.execute("SELECT id, username, password_hash FROM users WHERE email = ?", (username,))
            user = cursor.fetchone()
            
            if not user:
                print(f"No user found with email: {username}")
                return
            else:
                print(f"Found user by email instead: {user[1]}")
        
        # Check password
        if user[2] and check_password_hash(user[2], password):
            print("Password is correct! Login would succeed.")
        else:
            print("Password is incorrect or hash is invalid.")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    check_user_exists()
    
    # Ask for test credentials
    print("\n===== Test Login =====")
    test_username = input("Enter username or email to test: ")
    test_password = input("Enter password to test: ")
    
    if test_username and test_password:
        test_login(test_username, test_password)

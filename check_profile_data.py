import sqlite3
import json
import os
from flask import Flask
from datetime import datetime

# Create a minimal Flask app to access configuration
app = Flask(__name__)
app.config.from_pyfile('config.py')

def get_users_db_connection():
    """Get a connection to the users database."""
    try:
        # Try different possible database paths
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.db'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'users.db'),
            'users.db'  # Current directory
        ]
        
        # Print all possible paths for debugging
        print("Trying database paths:")
        for path in possible_paths:
            print(f"  - {path} (exists: {os.path.exists(path)})")
        
        # Try to connect to each path
        for path in possible_paths:
            if os.path.exists(path):
                print(f"Connecting to database at: {path}")
                conn = sqlite3.connect(path)
                conn.row_factory = sqlite3.Row
                return conn
        
        # If we get here, none of the paths worked
        print("Could not find users.db in any of the expected locations")
        
        # List all files in the current directory to help locate the database
        print("\nFiles in current directory:")
        for file in os.listdir(os.path.dirname(os.path.abspath(__file__))):
            if file.endswith('.db'):
                print(f"  - {file} (database file)")
            elif os.path.isdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), file)):
                print(f"  - {file}/ (directory)")
        
        return None
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return None

def check_user_profile(user_id=1):
    """Check user profile data in the database."""
    conn = get_users_db_connection()
    if not conn:
        print("Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Get table schema
        cursor.execute("PRAGMA table_info(users)")
        columns = [col[1] for col in cursor.fetchall()]
        print(f"\nUser table columns: {columns}\n")
        
        # Get user data
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user_data = cursor.fetchone()
        
        if not user_data:
            print(f"No user found with ID {user_id}")
            return
        
        # Convert to dictionary and print
        user_dict = {key: user_data[key] for key in user_data.keys()}
        
        # Format for better readability
        print("\nUser Profile Data:")
        print("-" * 50)
        for key, value in user_dict.items():
            print(f"{key}: {value}")
        
        # Check specific fields we're interested in
        print("\nKey Fields Check:")
        print("-" * 50)
        print(f"bio: {user_dict.get('bio')}")
        print(f"current_location_city: {user_dict.get('current_location_city')}")
        print(f"hometown: {user_dict.get('hometown')}")
        print(f"created_at: {user_dict.get('created_at')}")
        
    except Exception as e:
        print(f"Error checking user profile: {e}")
    finally:
        conn.close()

def update_profile_fields(user_id=1):
    """Update missing profile fields for testing."""
    conn = get_users_db_connection()
    if not conn:
        print("Failed to connect to database")
        return
    
    try:
        cursor = conn.cursor()
        
        # Check if fields exist and update them
        updates = {
            "bio": "This is a test bio for the profile page.",
            "current_location_city": "San Francisco",
            "hometown": "Seattle",
        }
        
        # Prepare SQL update statement
        set_clauses = [f"{key} = ?" for key in updates.keys()]
        query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = ?"
        
        # Execute update
        cursor.execute(query, list(updates.values()) + [user_id])
        conn.commit()
        
        print(f"\nUpdated user profile with test data:")
        for key, value in updates.items():
            print(f"{key}: {value}")
        
        # Verify the update
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        updated_user = cursor.fetchone()
        
        if updated_user:
            print("\nVerification after update:")
            for key in updates.keys():
                print(f"{key}: {updated_user[key]}")
        
    except Exception as e:
        print(f"Error updating profile fields: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("Checking user profile data in the database...")
    check_user_profile()
    
    # Ask if user wants to update profile with test data
    response = input("\nDo you want to update the profile with test data? (y/n): ")
    if response.lower() == 'y':
        update_profile_fields()
        print("\nProfile updated. Check the profile page now.")
    else:
        print("\nNo changes made to the profile.")

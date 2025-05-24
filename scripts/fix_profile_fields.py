import logging
import os
import sqlite3
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(levelname)s - %(message)s')

# Default database path - change if needed
DB_PATH = "users.db"

def fix_profile_fields(user_id, updates):
    """
    Direct database fix for profile fields
    """
    logging.info(f"Fixing profile fields for user {user_id}")
    logging.info(f"Updates: {updates}")
    
    try:
        # Connect directly to the database
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            logging.error(f"User {user_id} not found")
            return False
            
        logging.info(f"Current values: {dict(user)}")
        
        # Execute update for each field separately
        for field, value in updates.items():
            if value is None:
                value = ""
                
            query = f"UPDATE users SET {field} = ? WHERE id = ?"
            logging.info(f"Executing: {query} with params {(value, user_id)}")
            
            cursor.execute(query, (value, user_id))
            logging.info(f"Rows affected: {cursor.rowcount}")
            
        # Commit changes
        conn.commit()
        
        # Verify changes
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        updated_user = cursor.fetchone()
        updated_dict = dict(updated_user)
        
        logging.info(f"After update: {updated_dict}")
        
        # Check if updates were applied
        for field, value in updates.items():
            if value is None:
                value = ""
                
            if updated_dict.get(field) != value:
                logging.error(f"Field {field} not updated correctly")
                logging.error(f"Expected: '{value}', Got: '{updated_dict.get(field)}'")
                return False
                
        return True
        
    except Exception as e:
        logging.error(f"Error fixing profile fields: {e}")
        if 'conn' in locals():
            conn.rollback()
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python fix_profile_fields.py <user_id> [field=value field2=value2 ...]")
        sys.exit(1)
        
    user_id = int(sys.argv[1])
    updates = {}
    
    for arg in sys.argv[2:]:
        if '=' in arg:
            field, value = arg.split('=', 1)
            updates[field] = value
            
    if not updates:
        print("No updates provided")
        print("Example: python fix_profile_fields.py 1 first_name=John last_name=Doe")
        sys.exit(1)
        
    success = fix_profile_fields(user_id, updates)
    
    if success:
        print("Fields updated successfully!")
    else:
        print("Failed to update fields. Check the logs for details.")

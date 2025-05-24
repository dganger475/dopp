import json
import os
import sqlite3
import sys

# Default paths - adjust if necessary
DEFAULT_USERS_DB_PATH = "users.db"

def diagnose_database():
    """Diagnose the database structure and contents"""
    
    print("=== DATABASE DIAGNOSTIC TOOL ===")
    print(f"Database path: {DEFAULT_USERS_DB_PATH}")
    
    # Check if database exists
    if not os.path.exists(DEFAULT_USERS_DB_PATH):
        print(f"ERROR: Database file not found at {DEFAULT_USERS_DB_PATH}")
        return
        
    try:
        # Connect to the database
        conn = sqlite3.connect(DEFAULT_USERS_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check users table
        print("\n[1] Checking 'users' table...")
        try:
            cursor.execute("PRAGMA table_info(users)")
            columns = cursor.fetchall()
            
            if not columns:
                print("ERROR: 'users' table not found")
                return
                
            print(f"Found {len(columns)} columns in 'users' table:")
            for col in columns:
                print(f"  - {col['name']} ({col['type']})")
                
            # Check problematic fields specifically
            problem_fields = ['first_name', 'last_name', 'birthdate', 'hometown', 'current_location']
            for field in problem_fields:
                found = any(col['name'] == field for col in columns)
                field_type = next((col['type'] for col in columns if col['name'] == field), None)
                print(f"  - {field}: {'FOUND' if found else 'MISSING'} (Type: {field_type or 'N/A'})")
                
            # Check for NULL values in problematic fields
            print("\n[2] Checking for NULL values in problematic fields...")
            for field in problem_fields:
                cursor.execute(f"SELECT COUNT(*) FROM users WHERE {field} IS NULL")
                null_count = cursor.fetchone()[0]
                cursor.execute(f"SELECT COUNT(*) FROM users")
                total_count = cursor.fetchone()[0]
                print(f"  - {field}: {null_count}/{total_count} NULL values")
                
            # Print sample user data
            print("\n[3] Sample user data:")
            cursor.execute("SELECT id, username, first_name, last_name, birthdate, hometown, current_location FROM users LIMIT 3")
            users = cursor.fetchall()
            
            for user in users:
                user_dict = dict(user)
                print(f"  User {user_dict['id']} ({user_dict['username']}):")
                for field in problem_fields:
                    value = user_dict.get(field)
                    print(f"    - {field}: '{value}' (Type: {type(value).__name__})")
                    
            # Try a direct update to test
            print("\n[4] Testing direct update on first user...")
            user_id = users[0]['id'] if users else None
            
            if user_id:
                test_values = {
                    'first_name': 'TestFirstName',
                    'last_name': 'TestLastName',
                    'birthdate': '2000-01-01',
                    'hometown': 'TestHometown',
                    'current_location': 'TestLocation'
                }
                
                # Store original values
                originals = {}
                for field in problem_fields:
                    originals[field] = users[0][field]
                
                # Try update
                try:
                    for field, value in test_values.items():
                        print(f"  Updating {field} to '{value}'...")
                        cursor.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, user_id))
                        print(f"    - Rows affected: {cursor.rowcount}")
                    
                    conn.commit()
                    
                    # Verify update
                    cursor.execute(f"SELECT * FROM users WHERE id = ?", (user_id,))
                    updated_user = cursor.fetchone()
                    
                    if updated_user:
                        print("  Values after update:")
                        for field in problem_fields:
                            print(f"    - {field}: '{updated_user[field]}' (Type: {type(updated_user[field]).__name__})")
                    else:
                        print("  ERROR: User not found after update")
                        
                    # Restore original values
                    print("  Restoring original values...")
                    for field, value in originals.items():
                        cursor.execute(f"UPDATE users SET {field} = ? WHERE id = ?", (value, user_id))
                    
                    conn.commit()
                    
                except Exception as e:
                    print(f"  ERROR during test update: {e}")
                    conn.rollback()
            else:
                print("  No users found to test update")
                
        except Exception as e:
            print(f"ERROR checking users table: {e}")
            
    except Exception as e:
        print(f"ERROR connecting to database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()
            
    print("\n=== END OF DIAGNOSTIC ===")

if __name__ == "__main__":
    diagnose_database()

import sqlite3
import os
from utils.db.database import get_users_db_connection

# Get database connection
conn = get_users_db_connection()

if conn:
    cursor = conn.cursor()
    
    # Check posts table schema
    cursor.execute('PRAGMA table_info(posts)')
    columns = cursor.fetchall()
    
    print('Posts table schema:')
    for col in columns:
        # Convert sqlite3.Row to dictionary for easier viewing
        col_dict = {}
        for key in col.keys():
            col_dict[key] = col[key]
        print(col_dict)
    
    # Check if a sample post can be created
    try:
        test_data = {
            'user_id': 1,
            'content': 'Test post from schema checker',
            'is_match_post': 1,
            'face_filename': 'test_face.jpg'
        }
        
        # Build the query
        columns = list(test_data.keys())
        placeholders = ['?'] * len(columns)
        values = list(test_data.values())
        
        query = f"INSERT INTO posts ({', '.join(columns)}) VALUES ({', '.join(placeholders)})"
        print(f"\nTest query: {query}")
        print(f"Test values: {values}")
        
        # Execute the query but don't commit
        cursor.execute(query, values)
        print("\nTest insert succeeded!")
        
    except Exception as e:
        print(f"\nTest insert failed: {e}")
    finally:
        # Roll back any changes
        conn.rollback()
    
    conn.close()
else:
    print("Failed to connect to database")

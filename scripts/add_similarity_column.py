#!/usr/bin/env python3
"""
Add missing similarity column to user_matches table and set default values
"""

import logging
import os
import sqlite3
import sys

# Set up basic logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define database paths using hardcoded path from app.py
ROOT_DIR = r"C:\Users\1439\Documents\DopplegangerApp"
USERS_DB_PATH = os.path.join(ROOT_DIR, 'users.db')

def get_db_connection(db_path):
    """Connect to the specified SQLite database."""
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None

def check_table_schema():
    """Check if similarity column exists in user_matches table"""
    conn = get_db_connection(USERS_DB_PATH)
    if not conn:
        return False, "Failed to connect to database"
    
    try:
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(user_matches)")
        columns = cursor.fetchall()
        
        # Log all columns
        logger.info("Current columns in user_matches table:")
        for col in columns:
            logger.info(f"  {col['name']} ({col['type']})")
        
        # Check if similarity column exists
        has_similarity = any(col['name'] == 'similarity' for col in columns)
        return has_similarity, columns
    except Exception as e:
        logger.error(f"Error checking schema: {e}")
        return False, f"Error: {str(e)}"
    finally:
        if conn:
            conn.close()

def add_similarity_column():
    """Add similarity column to user_matches table if it doesn't exist"""
    has_similarity, columns_info = check_table_schema()
    
    if isinstance(columns_info, str):
        return columns_info  # Error message
    
    if has_similarity:
        logger.info("Similarity column already exists in user_matches table")
        return "Similarity column already exists"
    
    conn = get_db_connection(USERS_DB_PATH)
    if not conn:
        return "Failed to connect to database"
    
    try:
        cursor = conn.cursor()
        
        # Add similarity column with default NULL
        cursor.execute("ALTER TABLE user_matches ADD COLUMN similarity FLOAT")
        logger.info("Added similarity column to user_matches table")
        
        # Update all existing matches with a default similarity of 78.5
        cursor.execute("""
            UPDATE user_matches
            SET similarity = 78.5
        """)
        
        rows_updated = cursor.rowcount
        logger.info(f"Updated {rows_updated} matches with default similarity scores")
        
        # Commit changes
        conn.commit()
        
        # Verify column was added
        has_similarity, _ = check_table_schema()
        if has_similarity:
            return f"Successfully added similarity column and updated {rows_updated} matches"
        else:
            return "Failed to add similarity column"
    
    except Exception as e:
        logger.error(f"Error adding similarity column: {e}")
        if conn:
            conn.rollback()
        return f"Error: {str(e)}"
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    print("\n=== ADDING SIMILARITY COLUMN ===")
    result = add_similarity_column()
    print(f"\nResult: {result}")
    
    print("\n=== DONE ===")

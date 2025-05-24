"""
Fix decade values in the database.

This script finds and fixes incorrectly formatted decade values (5-digit decades)
by recalculating them using the correct formula.
"""

import logging
import os
import re
import sqlite3

logging.basicConfig(level=logging.INFO)

def get_decade_from_year(year_str):
    """
    Extract decade from a year string using the corrected formula
    
    Args:
        year_str: Year as a string
        
    Returns:
        Decade string (e.g., "1990s") or "Unknown"
    """
    if not year_str:
        return "Unknown"
    
    try:
        year = int(year_str)
        # Correct formula: Get the first 3 digits then add "0s"
        return f"{(year // 10)}0s"
    except (ValueError, TypeError):
        # Check if year might be embedded in the string (e.g., "Class of 1985")
        match = re.search(r'19\d{2}|20\d{2}', str(year_str))
        if match:
            year = int(match.group(0))
            return f"{(year // 10)}0s"
        return "Unknown"

def fix_decades_in_database():
    """Fix any 5-digit decades in the database tables."""
    db_path = os.path.join(os.path.dirname(__file__), 'faces.db')
    users_db_path = os.path.join(os.path.dirname(__file__), 'users.db')
    
    # Check if the faces database exists
    if os.path.exists(db_path):
        logging.info(f"Fixing decades in faces database: {db_path}")
        fix_decades_in_faces_db(db_path)
    else:
        logging.warning(f"Faces database not found at: {db_path}")
    
    # Check if the users database exists
    if os.path.exists(users_db_path):
        logging.info(f"Fixing decades in users database: {users_db_path}")
        fix_decades_in_users_db(users_db_path)
    else:
        logging.warning(f"Users database not found at: {users_db_path}")

def fix_decades_in_faces_db(db_path):
    """Fix decade values in the faces database."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if the faces table has a decade column
        cursor.execute("PRAGMA table_info(faces)")
        columns = cursor.fetchall()
        has_decade_column = any(col['name'] == 'decade' for col in columns)
        
        if has_decade_column:
            # Find faces with decade value that might be 5 digits
            cursor.execute("SELECT id, yearbook_year, decade FROM faces WHERE decade LIKE '%5s' OR decade LIKE '%1s' OR decade LIKE '%3s' OR decade LIKE '%7s' OR decade LIKE '%9s'")
            faces = cursor.fetchall()
            
            logging.info(f"Found {len(faces)} faces with potentially incorrect decade values")
            
            # Update each face with a corrected decade value
            for face in faces:
                if face['yearbook_year']:
                    new_decade = get_decade_from_year(face['yearbook_year'])
                    logging.info(f"Updating face {face['id']}: {face['decade']} -> {new_decade}")
                    cursor.execute("UPDATE faces SET decade = ? WHERE id = ?", (new_decade, face['id']))
        
        # Now, update any faces that don't have a decade value but do have a yearbook_year
        cursor.execute("SELECT id, yearbook_year FROM faces WHERE (decade IS NULL OR decade = 'Unknown') AND yearbook_year IS NOT NULL")
        faces = cursor.fetchall()
        
        logging.info(f"Found {len(faces)} faces with missing decade values")
        
        for face in faces:
            new_decade = get_decade_from_year(face['yearbook_year'])
            logging.info(f"Setting decade for face {face['id']} to {new_decade}")
            cursor.execute("UPDATE faces SET decade = ? WHERE id = ?", (new_decade, face['id']))
        
        conn.commit()
        logging.info("Finished updating faces database")
        
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

def fix_decades_in_users_db(db_path):
    """Check for any decade values in the users database tables."""
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # List all tables in the database
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table['name']
            # Check table structure for decade column
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            
            decade_columns = [col['name'] for col in columns if 'decade' in col['name'].lower()]
            
            for col_name in decade_columns:
                logging.info(f"Found decade column in table {table_name}: {col_name}")
                
                # Find rows with potentially incorrect decade values
                cursor.execute(f"SELECT id, {col_name} FROM {table_name} WHERE {col_name} LIKE '%5s' OR {col_name} LIKE '%1s' OR {col_name} LIKE '%3s' OR {col_name} LIKE '%7s' OR {col_name} LIKE '%9s'")
                rows = cursor.fetchall()
                
                logging.info(f"Found {len(rows)} rows with potentially incorrect decade values in {table_name}.{col_name}")
                
                # Update each row with a corrected decade value
                for row in rows:
                    old_decade = row[col_name]
                    # Extract year from the decade (e.g., 20105s -> 2010)
                    year_match = re.search(r'(\d+)s', old_decade)
                    if year_match:
                        year = int(year_match.group(1))
                        new_decade = get_decade_from_year(year)
                        logging.info(f"Updating {table_name} {row['id']}: {old_decade} -> {new_decade}")
                        cursor.execute(f"UPDATE {table_name} SET {col_name} = ? WHERE id = ?", (new_decade, row['id']))
        
        conn.commit()
        logging.info("Finished updating users database")
        
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    fix_decades_in_database()
    print("Database decade values have been fixed.")

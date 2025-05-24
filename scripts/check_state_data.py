import logging
import os
import sqlite3
import sys

# Set up path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_state_data():
    """Check the state data in the database and print statistics."""
    try:
        # Connect directly to the database
        db_path = os.path.join(parent_dir, 'faces.db')
        logging.info(f"Checking database at: {db_path}")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check if state column exists
        cursor.execute("PRAGMA table_info(faces)")
        columns = [col['name'] for col in cursor.fetchall()]
        if 'state' not in columns:
            logging.error("State column doesn't exist in the faces table!")
            return
        
        # Get state distribution
        cursor.execute("SELECT state, COUNT(*) as count FROM faces GROUP BY state")
        state_counts = cursor.fetchall()
        
        logging.info("STATE DATA DISTRIBUTION:")
        for row in state_counts:
            state_name = row['state'] or "NULL/EMPTY"
            count = row['count']
            logging.info(f"{state_name}: {count} faces")
        
        # Check a sample of matches from a user to see if they have state data
        # First get a user match
        user_db_path = os.path.join(parent_dir, 'users.db')
        user_conn = sqlite3.connect(user_db_path)
        user_conn.row_factory = sqlite3.Row
        user_cursor = user_conn.cursor()
        
        user_cursor.execute("SELECT * FROM user_matches LIMIT 5")
        user_matches = user_cursor.fetchall()
        
        if user_matches:
            logging.info("\nCHECKING SAMPLE USER MATCHES:")
            for match in user_matches:
                filename = match['match_filename']
                cursor.execute("SELECT * FROM faces WHERE filename = ?", (filename,))
                face = cursor.fetchone()
                
                if face:
                    logging.info(f"Match: {filename}")
                    logging.info(f"  - State: {face['state'] or 'NULL/EMPTY'}")
                    if 'decade' in columns:
                        logging.info(f"  - Decade: {face['decade'] or 'NULL/EMPTY'}")
                else:
                    logging.info(f"Match {filename} not found in faces database!")
        
        # Close connections
        conn.close()
        user_conn.close()
        
    except Exception as e:
        logging.error(f"Error checking state data: {e}")

if __name__ == "__main__":
    logging.info("Starting state data check")
    check_state_data()
    logging.info("State data check complete")

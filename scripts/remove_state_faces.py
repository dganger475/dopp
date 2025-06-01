"""
Script to remove faces from specific states (TX and IL) from the local extracted_faces folder and the faces.db file.
Uses parallel processing with 15 workers to speed up the deletion process.
"""

import os
import sqlite3
from dotenv import load_dotenv
from tqdm import tqdm
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('state_removal.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the SQLite database."""
    try:
        # Try multiple possible database locations
        possible_paths = [
            'faces.db',
            'instance/faces.db',
            os.path.join(os.path.dirname(__file__), '..', 'faces.db'),
            os.path.join(os.path.dirname(__file__), '..', 'instance', 'faces.db')
        ]
        
        for db_path in possible_paths:
            if os.path.exists(db_path):
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                return conn
                
        logger.error("Could not find database file in any of the expected locations")
        return None
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def process_face(face, extracted_faces_dir, conn):
    """Process a single face: delete from local folder and database."""
    try:
        # Double check the state
        if face['state'] not in ['TX', 'IL']:
            logger.warning(f"Skipping face {face['id']} with state {face['state']} (not in removal list)")
            return False
        
        logger.info(f"Processing face {face['id']} from state {face['state']}")
        
        # Delete from local folder
        local_path = os.path.join(extracted_faces_dir, face['filename'])
        if os.path.exists(local_path):
            os.remove(local_path)
            logger.info(f"Deleted file from local folder: {face['filename']}")
        else:
            logger.warning(f"File not found in local folder: {local_path}")
        
        # Delete from database
        cursor = conn.cursor()
        cursor.execute("DELETE FROM faces WHERE id = ?", (face['id'],))
        logger.info(f"Deleted face from database: ID {face['id']} (State: {face['state']})")
        
        # Add a small delay between operations to avoid rate limits
        time.sleep(0.1)
        
        return True
    except Exception as e:
        logger.error(f"Error processing face {face['id']}: {e}")
        return False

def remove_state_faces(states_to_remove=['TX', 'IL'], max_workers=15, extracted_faces_dir='extracted_faces'):
    """Remove faces from specified states from the local extracted_faces folder and the faces.db file using parallel processing."""
    # Load environment variables
    load_dotenv()
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection")
        return
    
    try:
        cursor = conn.cursor()
        
        # First, let's verify the states in the database
        cursor.execute("SELECT DISTINCT state FROM faces WHERE state IS NOT NULL")
        all_states = [row['state'] for row in cursor.fetchall()]
        logger.info(f"All states in database: {', '.join(all_states)}")
        
        # Get all faces from specified states
        placeholders = ','.join(['?' for _ in states_to_remove])
        query = f"SELECT id, filename, state FROM faces WHERE state IN ({placeholders})"
        cursor.execute(query, states_to_remove)
        faces = cursor.fetchall()
        
        if not faces:
            logger.info(f"No faces found for states: {', '.join(states_to_remove)}")
            return
        
        # Count faces by state
        state_counts = Counter(face['state'] for face in faces)
        logger.info(f"Found faces by state: {dict(state_counts)}")
        
        # Process faces in parallel
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_face, face, extracted_faces_dir, conn) for face in faces]
            
            # Monitor progress with tqdm
            for future in tqdm(as_completed(futures), total=len(futures), desc="Removing faces"):
                future.result()  # Wait for each task to complete
        
        # Commit changes
        conn.commit()
        logger.info("Successfully completed face removal process")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    remove_state_faces(max_workers=15, extracted_faces_dir='extracted_faces') 
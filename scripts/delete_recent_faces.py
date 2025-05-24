import logging
import os
import sqlite3
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime, timedelta

from tqdm import tqdm

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def delete_face(data):
    """Delete a single face file and return its filename for database cleanup."""
    filename, image_path, cutoff_time = data
    try:
        if os.path.exists(image_path):
            file_time = datetime.fromtimestamp(os.path.getctime(image_path))
            if file_time > cutoff_time:
                os.remove(image_path)
                return filename
    except Exception as e:
        logging.error(f"Error processing {filename}: {e}")
    return None

def delete_recent_faces():
    """Delete faces created in the last 2 days using parallel processing."""
    
    # Calculate timestamp from 2 days ago
    two_days_ago = datetime.now() - timedelta(days=2)
    
    # Connect to database
    conn = sqlite3.connect('faces.db')
    cursor = conn.cursor()
    
    try:
        # Get total count first
        cursor.execute("SELECT COUNT(*) FROM faces")
        total_faces = cursor.fetchone()[0]
        logging.info(f"Total faces in database: {total_faces}")
        
        # Get list of all files to check
        cursor.execute("SELECT filename, image_path FROM faces")
        faces = cursor.fetchall()
        
        if not faces:
            logging.info("No faces found to delete")
            return
            
        logging.info(f"Checking {len(faces)} faces for recent ones...")
        
        # Prepare data for parallel processing
        process_data = [(f, p, two_days_ago) for f, p in faces]
        
        # Use ProcessPoolExecutor for parallel processing
        deleted_files = []
        with ProcessPoolExecutor(max_workers=os.cpu_count() - 1) as executor:
            # Submit all tasks and get futures
            futures = [executor.submit(delete_face, data) for data in process_data]
            
            # Process results with progress bar
            with tqdm(total=len(futures), desc="Deleting faces") as pbar:
                for future in as_completed(futures):
                    result = future.result()
                    if result:
                        deleted_files.append(result)
                    pbar.update(1)
        
        # Batch delete from database
        if deleted_files:
            placeholders = ','.join('?' * len(deleted_files))
            cursor.execute(f"DELETE FROM faces WHERE filename IN ({placeholders})", deleted_files)
            conn.commit()
            
        logging.info(f"Successfully deleted {len(deleted_files)} faces from the last 2 days")
        logging.info(f"Remaining faces in database: {total_faces - len(deleted_files)}")
        
    except Exception as e:
        logging.error(f"Error during deletion: {e}")
        
    finally:
        conn.close()

if __name__ == "__main__":
    print("Starting deletion of faces from the last 2 days...")
    delete_recent_faces()
    print("Deletion complete!") 
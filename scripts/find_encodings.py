import logging
import os
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def find_encodings():
    """Find where the new face encodings might be stored"""
    try:
        # Define paths
        app_dir = Path(r'C:\Users\1439\Documents\DopplegangerApp')
        old_faces_dir = app_dir / 'static' / 'extracted_faces'
        new_faces_dir = app_dir / 'extracted_faces'
        main_db = app_dir / 'faces.db'
        
        # Count faces in each directory
        old_faces = [f.name for f in old_faces_dir.glob('*.jpg') if not f.name.startswith('display_')]
        new_faces = [f.name for f in new_faces_dir.glob('*.jpg') if not f.name.startswith('display_')]
        
        logging.info("\nFolder Summary:")
        logging.info(f"Original faces folder ({old_faces_dir}): {len(old_faces):,} images")
        logging.info(f"New faces folder ({new_faces_dir}): {len(new_faces):,} images")
        
        # Check all .db files in the directory and subdirectories
        logging.info("\nSearching for database files...")
        db_files = list(app_dir.rglob('*.db'))
        
        for db_path in db_files:
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Check if this database has a faces table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='faces'")
                if cursor.fetchone():
                    # Get face counts and sample filenames
                    cursor.execute("SELECT COUNT(*) FROM faces")
                    total_faces = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT filename FROM faces LIMIT 5")
                    sample_files = [row[0] for row in cursor.fetchall()]
                    
                    logging.info(f"\nDatabase found: {db_path}")
                    logging.info(f"Total faces in database: {total_faces:,}")
                    logging.info("Sample filenames:")
                    for sample in sample_files:
                        logging.info(f"- {sample}")
                
                conn.close()
                
            except Exception as e:
                logging.error(f"Error checking database {db_path}: {e}")
        
        # Look for any test_faces.db or similar files
        test_dbs = list(app_dir.rglob('test*.db'))
        if test_dbs:
            logging.info("\nPossible test databases found:")
            for test_db in test_dbs:
                logging.info(f"- {test_db}")
        
    except Exception as e:
        logging.error(f"Error during search: {e}")

if __name__ == "__main__":
    find_encodings() 
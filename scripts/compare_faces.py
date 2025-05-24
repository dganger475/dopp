import logging
import os
import sqlite3
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def compare_faces():
    """Compare faces in folder vs database"""
    try:
        # Get files from the correct folder
        faces_dir = Path(r'C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces')
        
        image_files = [f.name for f in faces_dir.glob('*.jpg') if not f.name.startswith('display_')]
        logging.info(f"\nFiles in folder: {len(image_files):,}")
        
        # Check database
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Get all filenames from database
        cursor.execute("SELECT filename FROM faces")
        db_files = {row[0] for row in cursor.fetchall()}
        
        # Find differences
        files_not_in_db = set(image_files) - db_files
        files_in_db_not_folder = db_files - set(image_files)
        
        logging.info("\nComparison Summary:")
        logging.info(f"Checking folder: {faces_dir}")
        logging.info(f"Files in folder: {len(image_files):,}")
        logging.info(f"Files in database: {len(db_files):,}")
        logging.info(f"Files in folder but not in database: {len(files_not_in_db):,}")
        logging.info(f"Files in database but not in folder: {len(files_in_db_not_folder):,}")
        
        if files_not_in_db:
            logging.info("\nSample of files missing from database:")
            for f in list(files_not_in_db)[:5]:
                logging.info(f"- {f}")
        
        if files_in_db_not_folder:
            logging.info("\nSample of files in database but missing from folder:")
            for f in list(files_in_db_not_folder)[:5]:
                logging.info(f"- {f}")
                
        # Check other possible database files
        possible_dbs = list(Path('.').glob('*.db'))
        if len(possible_dbs) > 1:
            logging.info("\nOther database files found:")
            for db in possible_dbs:
                if db.name != 'faces.db':
                    try:
                        test_conn = sqlite3.connect(db)
                        test_cursor = test_conn.cursor()
                        test_cursor.execute("SELECT COUNT(*) FROM faces")
                        count = test_cursor.fetchone()[0]
                        logging.info(f"- {db.name}: {count:,} faces")
                        test_conn.close()
                    except:
                        logging.info(f"- {db.name}: Unable to read")
        
    except Exception as e:
        logging.error(f"Error during comparison: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    compare_faces()

import logging
import os
import sqlite3

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def cleanup_database():
    """Clean up database by removing invalid entries."""
    try:
        # Connect to database
        conn = sqlite3.connect('faces.db', timeout=20)
        cursor = conn.cursor()
        
        # First, let's see what we actually have
        cursor.execute("SELECT COUNT(*) FROM faces")
        total_entries = cursor.fetchone()[0]
        logging.info(f"Total entries before cleanup: {total_entries}")
        
        # Get all entries with their encodings
        cursor.execute("SELECT id, filename, image_path, encoding FROM faces")
        entries = cursor.fetchall()
        
        deleted_count = 0
        asec_count = 0
        missing_file_count = 0
        no_encoding_count = 0
        
        for entry_id, filename, image_path, encoding in entries:
            should_delete = False
            
            # Check if encoding is None or empty
            if encoding is None or len(encoding) == 0:
                logging.info(f"No encoding for: {filename}")
                should_delete = True
                no_encoding_count += 1
            
            # Check if file exists
            if not os.path.exists(image_path):
                logging.info(f"Missing image file: {image_path}")
                should_delete = True
                missing_file_count += 1
            
            # Check for 'asec10' in filename
            if 'asec10' in filename.lower():
                logging.info(f"Found asec10 in filename: {filename}")
                should_delete = True
                asec_count += 1
            
            if should_delete:
                # Delete from database
                cursor.execute("DELETE FROM faces WHERE id = ?", (entry_id,))
                deleted_count += 1
                
                # Try to delete file if it exists
                if os.path.exists(image_path):
                    try:
                        os.remove(image_path)
                        logging.info(f"Deleted file: {image_path}")
                    except Exception as e:
                        logging.error(f"Error deleting file {image_path}: {e}")
        
        # Commit changes
        conn.commit()
        
        # Get final count
        cursor.execute("SELECT COUNT(*) FROM faces")
        remaining_entries = cursor.fetchone()[0]
        
        logging.info("\nCleanup Summary:")
        logging.info(f"- Initial total entries: {total_entries}")
        logging.info(f"- Entries deleted: {deleted_count}")
        logging.info(f"- Missing image files: {missing_file_count}")
        logging.info(f"- Missing encodings: {no_encoding_count}")
        logging.info(f"- Entries with 'asec10': {asec_count}")
        logging.info(f"- Remaining entries: {remaining_entries}")
        
    except Exception as e:
        logging.error(f"Error during cleanup: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_database() 
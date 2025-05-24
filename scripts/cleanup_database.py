import logging
import os
import sqlite3

from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='database_cleanup.log'
)

def cleanup_database():
    """Clean up the faces database by removing improper entries and verifying encodings"""
    print("Starting database cleanup...")
    
    # Connect to database
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    
    try:
        # Get total count before cleanup
        cursor.execute("SELECT COUNT(*) FROM faces")
        initial_count = cursor.fetchone()[0]
        print(f"Initial database entries: {initial_count}")
        
        # 1. Remove entries where the file doesn't exist
        print("\nRemoving entries with missing files...")
        cursor.execute("SELECT filename, image_path FROM faces")
        rows = cursor.fetchall()
        missing_files = 0
        
        for filename, image_path in tqdm(rows, desc="Checking files"):
            if not os.path.exists(image_path):
                cursor.execute("DELETE FROM faces WHERE filename = ?", (filename,))
                missing_files += 1
        
        print(f"Removed {missing_files} entries with missing files")
        
        # 2. Remove entries with improper naming format
        print("\nRemoving entries with improper naming...")
        cursor.execute("SELECT filename FROM faces")
        rows = cursor.fetchall()
        improper_names = 0
        
        for (filename,) in tqdm(rows, desc="Checking filenames"):
            parts = filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '').split('_')
            should_delete = False
            
            try:
                if len(parts) < 4:  # Need at least year, school, page, face
                    should_delete = True
                elif not (parts[0].isdigit() and len(parts[0]) == 4):  # First part should be year
                    should_delete = True
                elif not any(p.startswith('page') for p in parts):  # Should have 'page' somewhere
                    should_delete = True
                elif not any(p.startswith('face') for p in parts):  # Should have 'face' somewhere
                    should_delete = True
                elif len(''.join(parts[1:-2]).strip()) == 0:  # School name should not be empty
                    should_delete = True
                    
                if should_delete:
                    cursor.execute("DELETE FROM faces WHERE filename = ?", (filename,))
                    improper_names += 1
            except:
                cursor.execute("DELETE FROM faces WHERE filename = ?", (filename,))
                improper_names += 1
        
        print(f"Removed {improper_names} entries with improper naming")
        
        # 3. Remove entries with NULL or invalid encodings
        print("\nRemoving entries with invalid encodings...")
        cursor.execute("SELECT COUNT(*) FROM faces WHERE encoding IS NULL")
        null_encodings = cursor.fetchone()[0]
        cursor.execute("DELETE FROM faces WHERE encoding IS NULL")
        print(f"Removed {null_encodings} entries with NULL encodings")
        
        # Commit all changes
        conn.commit()
        
        # Get final count
        cursor.execute("SELECT COUNT(*) FROM faces")
        final_count = cursor.fetchone()[0]
        
        print("\nCleanup Summary:")
        print(f"Initial entries: {initial_count}")
        print(f"Removed missing files: {missing_files}")
        print(f"Removed improper names: {improper_names}")
        print(f"Removed NULL encodings: {null_encodings}")
        print(f"Final entries: {final_count}")
        print(f"Total removed: {initial_count - final_count}")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    cleanup_database() 
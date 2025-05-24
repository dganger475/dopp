import logging
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_database():
    """Check current database state"""
    try:
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM faces")
        total = cursor.fetchone()[0]
        logging.info(f"Current total entries: {total}")
        
        # Sample some remaining entries
        cursor.execute("SELECT filename, image_path FROM faces LIMIT 5")
        samples = cursor.fetchall()
        logging.info("\nSample entries:")
        for filename, path in samples:
            logging.info(f"- {filename}: {path}")
            
    except Exception as e:
        logging.error(f"Error checking database: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database() 
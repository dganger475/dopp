import logging
import sqlite3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_database():
    """Check face counts in database"""
    try:
        # Connect to database
        conn = sqlite3.connect('faces.db')
        cursor = conn.cursor()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM faces")
        total = cursor.fetchone()[0]
        
        # Get count of faces with encodings
        cursor.execute("SELECT COUNT(*) FROM faces WHERE encoding IS NOT NULL")
        with_encoding = cursor.fetchone()[0]
        
        # Get sample of filenames
        cursor.execute("SELECT filename FROM faces LIMIT 5")
        samples = cursor.fetchall()
        
        logging.info("\nDatabase Summary:")
        logging.info(f"Total faces: {total:,}")
        logging.info(f"Faces with encodings: {with_encoding:,}")
        logging.info(f"Faces without encodings: {total - with_encoding:,}")
        
        if samples:
            logging.info("\nSample entries:")
            for sample in samples:
                logging.info(f"- {sample[0]}")
            
    except Exception as e:
        logging.error(f"Error checking database: {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_database() 
"""
Script to re-upload face encodings to Supabase with new filenames.
This is more efficient than updating existing records.
"""

import os
import csv
import logging
import numpy as np
import sqlite3
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm
import time
from typing import List, Tuple, Dict
import json
import pickle

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('reupload_encodings.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """Initialize and return a Supabase client."""
    try:
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_ANON_KEY')
        if not url or not key:
            raise ValueError("Missing Supabase credentials in environment variables")
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Error connecting to Supabase: {e}")
        raise

def read_mapping_file(csv_path: str) -> List[Tuple[str, str]]:
    """Read the mapping file and return a list of (old_filename, new_filename) tuples."""
    mappings = []
    try:
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                mappings.append((row['old_filename'], row['new_filename']))
        logger.info(f"Read {len(mappings)} mappings from CSV")
        return mappings
    except Exception as e:
        logger.error(f"Error reading mapping file: {e}")
        raise

def get_db_connection():
    """Get a connection to the SQLite database."""
    try:
        db_path = r"C:\Users\1439\Documents\Dopp\faces.db"
        if not os.path.exists(db_path):
            logger.error(f"Database file not found at: {db_path}")
            return None
            
        logger.info(f"Connecting to database at: {db_path}")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        
        # Check if the faces table exists and has the right columns
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='faces'")
        if not cursor.fetchone():
            logger.error(f"Table 'faces' not found in {db_path}")
            return None
            
        cursor.execute("PRAGMA table_info(faces)")
        columns = [row['name'] for row in cursor.fetchall()]
        logger.info(f"Found columns in faces table: {columns}")
        
        if 'encoding' not in columns:
            logger.error(f"Column 'encoding' not found in faces table in {db_path}")
            return None
            
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

def load_encodings_from_db(conn: sqlite3.Connection, new_filenames: List[str]) -> Dict[str, np.ndarray]:
    """Load face encodings from SQLite database."""
    try:
        encodings = {}
        cursor = conn.cursor()
        
        # Debug: Print the first few filenames we're looking for
        logger.info(f"Looking for encodings for first few filenames: {new_filenames[:5]}")
        
        # Use parameterized query with IN clause
        placeholders = ','.join(['?' for _ in new_filenames])
        query = f"SELECT filename, encoding FROM faces WHERE filename IN ({placeholders})"
        
        cursor.execute(query, new_filenames)
        rows = cursor.fetchall()
        
        # Debug: Print the number of rows found
        logger.info(f"Found {len(rows)} matching rows in database")
        
        for row in rows:
            try:
                # Convert bytes to numpy array
                encoding_bytes = row['encoding']
                encoding = np.frombuffer(encoding_bytes, dtype=np.float32)
                encodings[row['filename']] = encoding
            except Exception as e:
                logger.error(f"Error processing encoding for {row['filename']}: {e}")
                continue
            
        logger.info(f"Successfully loaded {len(encodings)} encodings from database")
        return encodings
    except Exception as e:
        logger.error(f"Error loading encodings from database: {e}")
        raise

def reupload_encodings(supabase: Client, mappings: List[Tuple[str, str]], batch_size: int = 50):
    """Re-upload encodings to Supabase with new filenames."""
    total_mappings = len(mappings)
    processed = 0
    successful = 0
    failed = 0
    
    # Get database connection
    conn = get_db_connection()
    if not conn:
        raise ValueError("Could not connect to database")
    
    try:
        # Get the current max ID from Supabase
        try:
            result = supabase.table('faces').select('id').order('id', desc=True).limit(1).execute()
            if result.data:
                current_max_id = result.data[0]['id']
            else:
                current_max_id = 0
        except Exception as e:
            logger.error(f"Error getting max ID from Supabase: {e}")
            current_max_id = 0
            
        logger.info(f"Current max ID in Supabase: {current_max_id}")
        
        # Process in batches
        for i in tqdm(range(0, total_mappings, batch_size), desc="Uploading encodings"):
            batch = mappings[i:i + batch_size]
            new_filenames = [new for _, new in batch]  # Use new filenames instead of old ones
            
            # Load encodings for this batch
            encodings = load_encodings_from_db(conn, new_filenames)
            batch_data = []
            
            # Prepare batch data
            for old_filename, new_filename in batch:
                if new_filename in encodings:
                    current_max_id += 1
                    encoding = encodings[new_filename]
                    batch_data.append({
                        'id': current_max_id,  # Use sequential integer IDs
                        'filename': new_filename,
                        'encoding': encoding.tolist()  # Convert numpy array to list
                    })
                else:
                    logger.warning(f"No encoding found for {new_filename}")
            
            if batch_data:
                try:
                    # Insert new records
                    result = supabase.table('faces').insert(batch_data).execute()
                    
                    if hasattr(result, 'data'):
                        successful += len(result.data)
                    else:
                        logger.warning(f"Unexpected response format for batch {i//batch_size + 1}")
                    
                    processed += len(batch_data)
                    
                except Exception as e:
                    logger.error(f"Error uploading batch {i//batch_size + 1}: {e}")
                    failed += len(batch_data)
                    processed += len(batch_data)
            
            # Add a small delay between batches to avoid rate limits
            time.sleep(0.1)
    
    finally:
        conn.close()
    
    # Print summary
    summary = {
        'total': total_mappings,
        'processed': processed,
        'successful': successful,
        'failed': failed
    }
    
    summary_report = (
        f"\nSummary Report:\n"
        f"Total mappings: {summary['total']}\n"
        f"Processed: {summary['processed']}\n"
        f"Successfully uploaded: {summary['successful']}\n"
        f"Failed: {summary['failed']}\n"
    )
    print(summary_report)
    logger.info(summary_report)
    
    # Save summary to file
    with open('reupload_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

def main():
    """Main function to orchestrate the reupload process."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Read mapping file
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'b2_supabase_faiss_mapping.csv')
        mappings = read_mapping_file(csv_path)
        
        # Re-upload encodings
        reupload_encodings(supabase, mappings)
        
        logger.info("Successfully completed reuploading encodings")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main() 
"""
Script to rename files locally based on a CSV mapping, update the faces.db database,
and optionally upload the renamed files to a new B2 bucket.
Uses parallel processing with 15 workers to speed up the process.
"""

import os
import csv
import sqlite3
import b2sdk.v2 as b2
from dotenv import load_dotenv
from tqdm import tqdm
import logging
import time
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rename_and_upload.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def rate_limit(max_retries=3, delay=1):
    """Decorator to handle rate limiting with exponential backoff."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except b2.exception.DownloadCapExceeded as e:
                    retries += 1
                    if retries == max_retries:
                        logger.error(f"Max retries ({max_retries}) exceeded for rate limit")
                        raise
                    wait_time = delay * (2 ** retries)  # Exponential backoff
                    logger.warning(f"Rate limit hit, waiting {wait_time} seconds before retry {retries}/{max_retries}")
                    time.sleep(wait_time)
                except Exception as e:
                    raise
            return None
        return wrapper
    return decorator

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

def get_b2_bucket():
    """Get B2 bucket with proper configuration."""
    try:
        info = b2.InMemoryAccountInfo()
        b2_api = b2.B2Api(info)
        
        # Use environment variables for credentials
        application_key_id = os.getenv('B2_APPLICATION_KEY_ID')
        application_key = os.getenv('B2_APPLICATION_KEY')
        bucket_name = os.getenv('B2_BUCKET_NAME')
        
        b2_api.authorize_account("production", application_key_id, application_key)
        return b2_api.get_bucket_by_name(bucket_name)
    except Exception as e:
        logger.error(f"Error connecting to B2: {e}")
        return None

@rate_limit(max_retries=3, delay=2)
def upload_b2_file(bucket, local_path, b2_filename):
    """Upload a file to B2 with rate limiting."""
    try:
        bucket.upload_local_file(local_path, b2_filename)
        logger.info(f"Uploaded file to B2: {b2_filename}")
        return True
    except b2.exception.DownloadCapExceeded:
        raise  # Let the decorator handle the retry
    except Exception as e:
        logger.error(f"Error uploading to B2: {e}")
        return False

def process_file(file_info, local_dir, bucket=None, dry_run=False):
    """Process a single file: rename locally, update database, and optionally upload to B2."""
    old_filename, new_filename = file_info
    try:
        # Create a new database connection for this thread
        conn = get_db_connection()
        if not conn:
            logger.error(f"Failed to get database connection for {old_filename}")
            return False
            
        try:
            # Check if the new filename already exists
            new_path = os.path.join(local_dir, new_filename)
            file_already_renamed = os.path.exists(new_path)
            
            if not file_already_renamed:
                # Try different possible old filename formats
                possible_old_paths = [
                    os.path.join(local_dir, old_filename),  # Original format
                    os.path.join(local_dir, f"tin_{old_filename}"),  # With 'tin_' prefix
                    os.path.join(local_dir, old_filename.replace("University_of_Texas_Austin_", "tin_")),  # Replace prefix
                    os.path.join(local_dir, old_filename.replace("GeorgeFoxCollege", "GeorgeFox")),  # Fix college name
                    os.path.join(local_dir, old_filename.replace("_", " ")),  # Replace underscores with spaces
                    os.path.join(local_dir, old_filename.replace(" ", "_")),  # Replace spaces with underscores
                    os.path.join(local_dir, old_filename.lower()),  # Lowercase
                    os.path.join(local_dir, old_filename.upper()),  # Uppercase
                    os.path.join(local_dir, old_filename.replace("Yearbook", "")),  # Remove "Yearbook"
                    os.path.join(local_dir, old_filename.replace("Yearbook", "YB")),  # Replace "Yearbook" with "YB"
                    os.path.join(local_dir, old_filename.replace("faces_", "")),  # Remove "faces_"
                    os.path.join(local_dir, old_filename.replace("faces", "")),  # Remove "faces"
                    os.path.join(local_dir, old_filename.replace("_faces_", "_")),  # Remove "_faces_"
                    os.path.join(local_dir, old_filename.replace("_faces", "")),  # Remove "_faces"
                    os.path.join(local_dir, old_filename.replace("_face_", "_")),  # Remove "_face_"
                    os.path.join(local_dir, old_filename.replace("_face", "")),  # Remove "_face"
                    os.path.join(local_dir, old_filename.replace("_f", "_")),  # Remove "_f"
                    os.path.join(local_dir, old_filename.replace("_p", "_")),  # Remove "_p"
                    os.path.join(local_dir, old_filename.replace("_page_", "_")),  # Remove "_page_"
                    os.path.join(local_dir, old_filename.replace("_page", "")),  # Remove "_page"
                ]
                
                # Add variations with tin_ prefix
                tin_variations = [
                    os.path.join(local_dir, f"tin_{path.split('/')[-1]}") for path in possible_old_paths
                ]
                possible_old_paths.extend(tin_variations)
                
                old_path = None
                for path in possible_old_paths:
                    if os.path.exists(path):
                        old_path = path
                        break
                
                if not old_path:
                    logger.warning(f"Old file not found in any format: {old_filename}")
                    return False
                
                # Rename file locally
                try:
                    if not dry_run:
                        os.rename(old_path, new_path)
                    logger.info(f"Renamed file: {os.path.basename(old_path)} -> {new_filename}")
                except Exception as e:
                    logger.error(f"Error renaming file {os.path.basename(old_path)}: {e}")
                    return False
            else:
                logger.info(f"File already renamed: {new_filename}")
            
            # Update database - do this for both new and already renamed files
            try:
                if not dry_run:
                    cursor = conn.cursor()
                    # Update all matching filenames in the database
                    cursor.execute("""
                        UPDATE faces 
                        SET filename = ? 
                        WHERE filename IN (
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                        )
                    """, (
                        new_filename,  # 1 parameter for SET
                        old_filename,  # 20 parameters for IN clause
                        f"tin_{old_filename}",
                        old_filename.replace("University_of_Texas_Austin_", "tin_"),
                        old_filename.replace("GeorgeFoxCollege", "GeorgeFox"),
                        old_filename.replace("_", " "),
                        old_filename.replace(" ", "_"),
                        old_filename.lower(),
                        old_filename.upper(),
                        old_filename.replace("Yearbook", ""),
                        old_filename.replace("Yearbook", "YB"),
                        old_filename.replace("faces_", ""),
                        old_filename.replace("faces", ""),
                        old_filename.replace("_faces_", "_"),
                        old_filename.replace("_faces", ""),
                        old_filename.replace("_face_", "_"),
                        old_filename.replace("_face", ""),
                        old_filename.replace("_f", "_"),
                        old_filename.replace("_p", "_"),
                        old_filename.replace("_page_", "_"),
                        old_filename.replace("_page", "")  # Added this to make it 21 total
                    ))
                    conn.commit()  # Commit immediately for this file
                logger.info(f"Updated database for: {new_filename}")
            except Exception as e:
                logger.error(f"Error updating database for {new_filename}: {e}")
                return False
            
            # Upload to B2 if requested - do this for both new and already renamed files
            if bucket and not dry_run:
                upload_b2_file(bucket, new_path, new_filename)
            
            # Add a small delay between operations to avoid rate limits
            time.sleep(0.1)
            
            return True
        finally:
            conn.close()  # Always close the connection
            
    except Exception as e:
        logger.error(f"Error processing file {old_filename}: {e}")
        return False

def rename_files_and_update_db(csv_path, local_dir, upload_to_b2=False, max_workers=15, dry_run=False):
    """Rename files locally based on CSV mapping, update faces.db, and optionally upload to B2."""
    # Load environment variables
    load_dotenv()
    
    # Get B2 bucket if needed
    bucket = None
    if upload_to_b2 and not dry_run:
        bucket = get_b2_bucket()
        if not bucket:
            logger.error("Failed to get B2 bucket")
            return
    
    try:
        # Read CSV mapping
        with open(csv_path, 'r') as f:
            reader = csv.DictReader(f)
            mapping = [(row['old_filename'], row['new_filename']) for row in reader]
        
        logger.info(f"Loaded {len(mapping)} filename mappings from CSV")

        # Stats for summary report
        summary = {
            'total': len(mapping),
            'renamed': 0,
            'already_renamed': 0,
            'db_updated': 0,
            'uploaded': 0,
            'not_found': 0,
            'errors': 0
        }

        # Process files in parallel
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_file, file_info, local_dir, bucket, dry_run) for file_info in mapping]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Processing files"):
                res = future.result()
                results.append(res)

        # Aggregate summary
        for res in results:
            if res:
                summary['renamed'] += 1
                summary['db_updated'] += 1
                summary['uploaded'] += 1
            else:
                summary['not_found'] += 1
                summary['errors'] += 1

        # Print and log summary
        summary_report = (
            f"\nSummary Report:\n"
            f"Total files processed: {summary['total']}\n"
            f"Files renamed: {summary['renamed']}\n"
            f"Files already renamed: {summary['already_renamed']}\n"
            f"Database updated: {summary['db_updated']}\n"
            f"Files uploaded to B2: {summary['uploaded']}\n"
            f"Files not found: {summary['not_found']}\n"
            f"Errors: {summary['errors']}\n"
        )
        print(summary_report)
        logger.info(summary_report)
        logger.info("Successfully completed file renaming and database update")
    except Exception as e:
        logger.error(f"Error in main process: {e}")

if __name__ == "__main__":
    # Example usage
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'b2_supabase_faiss_mapping.csv')  # Path to your CSV mapping file
    local_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'extracted_faces')  # Updated path to extracted_faces
    upload_to_b2 = True  # Set to True to upload to B2
    dry_run = False  # Set to True to preview changes without making them
    
    rename_files_and_update_db(csv_path, local_dir, upload_to_b2, max_workers=15, dry_run=dry_run) 
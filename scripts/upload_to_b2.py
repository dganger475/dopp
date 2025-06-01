"""
Script to upload files from extracted_faces and profile_pics folders to Backblaze B2.
Uses parallel processing to speed up the upload process.
"""

import os
import b2sdk.v2 as b2
from dotenv import load_dotenv
from tqdm import tqdm
import logging
import time
from functools import wraps
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('b2_upload.log'),
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

def process_file(file_info, bucket):
    """Process a single file upload to B2."""
    local_path, b2_filename = file_info
    try:
        return upload_b2_file(bucket, local_path, b2_filename)
    except Exception as e:
        logger.error(f"Error processing file {local_path}: {e}")
        return False

def upload_folders_to_b2(folders_to_upload, max_workers=15):
    """Upload files from specified folders to B2."""
    # Load environment variables
    load_dotenv()
    
    # Get B2 bucket
    bucket = get_b2_bucket()
    if not bucket:
        logger.error("Failed to get B2 bucket")
        return
    
    try:
        # Collect all files to upload
        files_to_upload = []
        for folder_path, b2_prefix in folders_to_upload:
            if not os.path.exists(folder_path):
                logger.warning(f"Folder not found: {folder_path}")
                continue
                
            for root, _, files in os.walk(folder_path):
                for file in files:
                    local_path = os.path.join(root, file)
                    # Create B2 filename with appropriate prefix
                    rel_path = os.path.relpath(local_path, folder_path)
                    b2_filename = f"{b2_prefix}/{rel_path}"
                    files_to_upload.append((local_path, b2_filename))
        
        logger.info(f"Found {len(files_to_upload)} files to upload")

        # Stats for summary report
        summary = {
            'total': len(files_to_upload),
            'uploaded': 0,
            'errors': 0
        }

        # Process files in parallel
        results = []
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(process_file, file_info, bucket) for file_info in files_to_upload]
            for future in tqdm(as_completed(futures), total=len(futures), desc="Uploading files"):
                res = future.result()
                results.append(res)

        # Aggregate summary
        for res in results:
            if res:
                summary['uploaded'] += 1
            else:
                summary['errors'] += 1

        # Print and log summary
        summary_report = (
            f"\nSummary Report:\n"
            f"Total files processed: {summary['total']}\n"
            f"Files uploaded to B2: {summary['uploaded']}\n"
            f"Errors: {summary['errors']}\n"
        )
        print(summary_report)
        logger.info(summary_report)
        logger.info("Successfully completed file uploads to B2")
    except Exception as e:
        logger.error(f"Error in main process: {e}")

if __name__ == "__main__":
    # Define folders to upload with their B2 prefixes
    base_dir = os.path.join(os.path.dirname(__file__), '..')
    folders_to_upload = [
        (os.path.join(base_dir, 'static', 'extracted_faces'), 'extracted_faces'),
        (os.path.join(base_dir, 'static', 'profile_pics'), 'profile_pics')
    ]
    
    upload_folders_to_b2(folders_to_upload, max_workers=15) 
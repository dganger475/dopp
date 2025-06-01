"""
Script to update filenames in Supabase based on the mapping CSV file.
Uses batch processing to efficiently update the database.
"""

import os
import csv
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm
import time
from typing import List, Tuple, Dict
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('supabase_update.log'),
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

def update_supabase_filenames(supabase: Client, mappings: List[Tuple[str, str]], batch_size: int = 10, max_retries: int = 3):
    """Update filenames in Supabase in smaller batches with retry logic."""
    total_mappings = len(mappings)
    processed = 0
    successful = 0
    failed = 0
    retry_delay = 1  # Initial delay in seconds
    
    # Process in smaller batches
    for i in tqdm(range(0, total_mappings, batch_size), desc="Updating Supabase"):
        batch = mappings[i:i + batch_size]
        retries = 0
        
        while retries < max_retries:
            try:
                # Process each file in the batch individually
                for old_filename, new_filename in batch:
                    # Update faces table with single file
                    result = supabase.table('faces').update(
                        {'filename': new_filename}
                    ).eq('filename', old_filename).execute()
                    
                    # Log the result
                    if hasattr(result, 'data'):
                        successful += len(result.data)
                    else:
                        logger.warning(f"Unexpected response format for file {old_filename}")
                
                processed += len(batch)
                
                # Reset retry delay on success
                retry_delay = 1
                break
                
            except Exception as e:
                retries += 1
                if retries == max_retries:
                    logger.error(f"Failed to update batch {i//batch_size + 1} after {max_retries} retries: {e}")
                    failed += len(batch)
                    processed += len(batch)
                else:
                    logger.warning(f"Error updating batch {i//batch_size + 1}, retry {retries}/{max_retries}: {e}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
        
        # Add a small delay between batches to avoid rate limits
        time.sleep(0.5)
    
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
        f"Successfully updated: {summary['successful']}\n"
        f"Failed: {summary['failed']}\n"
    )
    print(summary_report)
    logger.info(summary_report)
    
    # Save summary to file
    with open('supabase_update_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

def main():
    """Main function to orchestrate the update process."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Read mapping file
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'b2_supabase_faiss_mapping.csv')
        mappings = read_mapping_file(csv_path)
        
        # Update Supabase with smaller batch size
        update_supabase_filenames(supabase, mappings, batch_size=10)
        
        logger.info("Successfully completed Supabase filename updates")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main() 
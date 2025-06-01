"""
Script to delete old records from Supabase after reuploading with new filenames.
This should be run after reupload_encodings.py has completed successfully.
"""

import os
import csv
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from tqdm import tqdm
import time
from typing import List, Tuple
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup_old_records.log'),
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

def delete_old_records(supabase: Client, mappings: List[Tuple[str, str]], batch_size: int = 100):
    """Delete old records from Supabase in batches."""
    total_mappings = len(mappings)
    processed = 0
    successful = 0
    failed = 0
    
    # Process in batches
    for i in tqdm(range(0, total_mappings, batch_size), desc="Deleting old records"):
        batch = mappings[i:i + batch_size]
        old_filenames = [old for old, _ in batch]
        
        try:
            # Delete records with old filenames
            result = supabase.table('faces').delete().in_('filename', old_filenames).execute()
            
            if hasattr(result, 'data'):
                successful += len(result.data)
            else:
                logger.warning(f"Unexpected response format for batch {i//batch_size + 1}")
            
            processed += len(batch)
            
        except Exception as e:
            logger.error(f"Error deleting batch {i//batch_size + 1}: {e}")
            failed += len(batch)
            processed += len(batch)
        
        # Add a small delay between batches to avoid rate limits
        time.sleep(0.1)
    
    # Print summary
    summary = {
        'total': total_mappings,
        'processed': processed,
        'successful': successful,
        'failed': failed
    }
    
    summary_report = (
        f"\nSummary Report:\n"
        f"Total old records to delete: {summary['total']}\n"
        f"Processed: {summary['processed']}\n"
        f"Successfully deleted: {summary['successful']}\n"
        f"Failed: {summary['failed']}\n"
    )
    print(summary_report)
    logger.info(summary_report)
    
    # Save summary to file
    with open('cleanup_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

def main():
    """Main function to orchestrate the cleanup process."""
    try:
        # Load environment variables
        load_dotenv()
        
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Read mapping file
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'b2_supabase_faiss_mapping.csv')
        mappings = read_mapping_file(csv_path)
        
        # Confirm with user
        print(f"\nAbout to delete {len(mappings)} old records from Supabase.")
        response = input("Do you want to continue? (yes/no): ")
        
        if response.lower() != 'yes':
            print("Cleanup cancelled.")
            return
        
        # Delete old records
        delete_old_records(supabase, mappings)
        
        logger.info("Successfully completed cleanup of old records")
        
    except Exception as e:
        logger.error(f"Error in main process: {e}")
        raise

if __name__ == "__main__":
    main() 
import os
import csv
import b2sdk.v2 as b2
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv
import sys
from datetime import datetime
import re
import tempfile
import shutil
from concurrent.futures import ThreadPoolExecutor, as_completed
from functools import partial
import threading
import argparse

# Debug: Print current working directory
print(f"Current working directory: {os.getcwd()}")

# Debug: Check if .env file exists and print its contents
env_path = os.path.join(os.getcwd(), '.env')
print(f"Looking for .env file at: {env_path}")
print(f".env file exists: {os.path.exists(env_path)}")

if os.path.exists(env_path):
    print("\nContents of .env file:")
    with open(env_path, 'r') as f:
        for line in f:
            # Only print non-empty lines that aren't comments
            if line.strip() and not line.strip().startswith('#'):
                # Mask sensitive values
                if 'KEY' in line or 'SECRET' in line:
                    key, value = line.split('=', 1)
                    print(f"{key}=***")
                else:
                    print(line.strip())

# Try to find .env file
dotenv_path = find_dotenv()
print(f"\nFound .env file at: {dotenv_path}")

# Load env variables with explicit path
load_dotenv(dotenv_path=dotenv_path, override=True)

# Debug: Print all environment variables
print("\nEnvironment variables:")
print(f"B2_APPLICATION_KEY_ID: {os.getenv('B2_APPLICATION_KEY_ID')}")
print(f"B2_APPLICATION_KEY: {os.getenv('B2_APPLICATION_KEY')}")
print(f"B2_BUCKET_NAME: {os.getenv('B2_BUCKET_NAME')}")

def validate_env_vars():
    """Validate that all required environment variables are present."""
    required_vars = ["B2_APPLICATION_KEY_ID", "B2_APPLICATION_KEY", "B2_BUCKET_NAME"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print("\nError: Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        print("\nPlease ensure these variables are set in your .env file")
        print("Make sure there are no spaces around the = sign")
        print("Example: B2_APPLICATION_KEY_ID=your_key_here")
        sys.exit(1)

def list_bucket_contents(bucket):
    """List all files in the bucket."""
    print("\nFiles in bucket:")
    for file_info, _ in bucket.ls():
        print(f"  - {file_info.file_name}")

def validate_and_update_mapping(bucket, mapping_path):
    """Validate mapping file against bucket contents and update if needed."""
    print("\nValidating mapping file against bucket contents...")
    
    # Get all files in bucket
    bucket_files = set()
    for file_info, _ in bucket.ls():
        bucket_files.add(file_info.file_name)
    
    # Read current mapping
    with open(mapping_path, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        rows = list(reader)
    
    # Track changes
    changes = []
    missing_files = []
    valid_rows = []
    
    # Validate each row
    for row in rows:
        old_name = row["old_filename"]
        if old_name in bucket_files:
            valid_rows.append(row)
        else:
            missing_files.append(old_name)
            # Try to find a similar file
            similar_files = [f for f in bucket_files if f.lower() == old_name.lower()]
            if similar_files:
                # Update the mapping with the correct case
                row["old_filename"] = similar_files[0]
                changes.append((old_name, similar_files[0]))
                valid_rows.append(row)
    
    # Report findings
    if missing_files:
        print(f"\nFound {len(missing_files)} files in mapping that don't exist in bucket:")
        for f in missing_files:
            print(f"  - {f}")
    
    if changes:
        print(f"\nFixed {len(changes)} filename case mismatches:")
        for old, new in changes:
            print(f"  - {old} -> {new}")
    
    # Update mapping file if needed
    if changes or missing_files:
        backup_path = f"{mapping_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"\nCreating backup of mapping file: {backup_path}")
        os.rename(mapping_path, backup_path)
        
        print(f"Updating mapping file with {len(valid_rows)} valid entries...")
        with open(mapping_path, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=reader.fieldnames)
            writer.writeheader()
            writer.writerows(valid_rows)
        
        print("Mapping file updated successfully!")
    
    return len(valid_rows) > 0

def generate_mapping_from_bucket(bucket, output_path, year_pattern=None, school_pattern=None):
    """Generate mapping file from bucket contents."""
    print("\nGenerating mapping file from bucket contents...")
    
    # Get all files in bucket
    bucket_files = []
    for file_info, _ in bucket.ls():
        bucket_files.append(file_info.file_name)
    
    # Sort files for consistent numbering
    bucket_files.sort()
    
    # Generate new filenames and extract metadata
    rows = []
    for i, old_name in enumerate(bucket_files, 1):
        # Generate new filename with padding
        new_name = f"face_{i:06d}.jpg"
        
        # Try to extract year and school from filename
        year = None
        school = None
        
        if year_pattern:
            year_match = re.search(year_pattern, old_name)
            if year_match:
                year = year_match.group(1)
        
        if school_pattern:
            school_match = re.search(school_pattern, old_name)
            if school_match:
                school = school_match.group(1)
        
        rows.append({
            'old_filename': old_name,
            'new_filename': new_name,
            'year': year or '',
            'school': school or ''
        })
    
    # Create backup if file exists
    if os.path.exists(output_path):
        backup_path = f"{output_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        print(f"Creating backup of existing mapping file: {backup_path}")
        os.rename(output_path, backup_path)
    
    # Write mapping file
    print(f"Writing mapping file with {len(rows)} entries...")
    with open(output_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['old_filename', 'new_filename', 'year', 'school'])
        writer.writeheader()
        writer.writerows(rows)
    
    print("Mapping file generated successfully!")
    return len(rows)

def process_single_file(bucket, temp_dir, row):
    """Process a single file with error handling."""
    old_name = row["old_filename"]
    new_name = row["new_filename"]
    
    try:
        # Download old file to temporary location
        temp_file_path = os.path.join(temp_dir, old_name)
        downloaded_file = bucket.download_file_by_name(old_name)
        downloaded_file.save_to(temp_file_path)
        
        # Upload with new name
        with open(temp_file_path, 'rb') as f:
            bucket.upload_bytes(f.read(), new_name)
        
        # Delete old file
        file_version = bucket.get_file_info_by_name(old_name)
        bucket.delete_file_version(file_version.id_, old_name)
        
        return True, old_name, None
        
    except b2.exception.FileNotPresent as e:
        error_msg = f"File not found"
        return False, old_name, error_msg
    except Exception as e:
        error_msg = str(e)
        return False, old_name, error_msg

def process_files_in_batches(mapping_path, batch_size=100, generate_mapping=False, max_workers=10):
    # Validate environment variables
    validate_env_vars()
    
    # Read B2 credentials from .env
    B2_KEY_ID = os.getenv("B2_APPLICATION_KEY_ID")
    B2_APP_KEY = os.getenv("B2_APPLICATION_KEY")
    B2_BUCKET_NAME = os.getenv("B2_BUCKET_NAME")
    
    try:
        # Set up B2 with thread-safe configuration
        info = b2.InMemoryAccountInfo()
        b2_api = b2.B2Api(info)
        
        # Authorize account with better error handling
        try:
            b2_api.authorize_account("production", B2_KEY_ID, B2_APP_KEY)
        except b2.exception.InvalidAuthToken as e:
            print("Error: Invalid B2 credentials")
            print("Please check your B2_APPLICATION_KEY_ID and B2_APPLICATION_KEY in the .env file")
            sys.exit(1)
        except Exception as e:
            print(f"Error authorizing B2 account: {str(e)}")
            sys.exit(1)
        
        # Get bucket with error handling
        try:
            bucket = b2_api.get_bucket_by_name(B2_BUCKET_NAME)
        except b2.exception.BucketNotFound as e:
            print(f"Error: Bucket '{B2_BUCKET_NAME}' not found")
            print("Please check your B2_BUCKET_NAME in the .env file")
            sys.exit(1)
        except Exception as e:
            print(f"Error accessing bucket: {str(e)}")
            sys.exit(1)
        
        # List bucket contents
        list_bucket_contents(bucket)
        
        if generate_mapping:
            # Generate mapping file from bucket contents
            year_pattern = r'(\d{4})'  # Matches 4-digit year
            school_pattern = r'([A-Za-z]+HS)'  # Matches school names ending in HS
            generate_mapping_from_bucket(bucket, mapping_path, year_pattern, school_pattern)
        
        # Validate and update mapping file
        if not validate_and_update_mapping(bucket, mapping_path):
            print("No valid files found in mapping. Exiting.")
            sys.exit(1)
        
        # Load updated mapping
        try:
            with open(mapping_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
        except FileNotFoundError:
            print(f"Error: Mapping file '{mapping_path}' not found")
            sys.exit(1)
        except Exception as e:
            print(f"Error reading mapping file: {str(e)}")
            sys.exit(1)
        
        # Create temporary directory for downloads
        with tempfile.TemporaryDirectory() as temp_dir:
            # Process in batches with parallel execution
            total_files = len(rows)
            processed_files = 0
            errors = []
            
            # Create a thread-safe progress bar
            progress_lock = threading.Lock()
            progress_bar = tqdm(total=total_files, desc="Processing files")
            
            def update_progress(success, old_name, error_msg):
                with progress_lock:
                    progress_bar.update(1)
                    if not success:
                        errors.append((old_name, error_msg))
                        with open("b2_rename_errors.log", "a") as f:
                            f.write(f"{old_name},,{error_msg}\n")
            
            # Process files in parallel
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Create a partial function with the common arguments
                process_func = partial(process_single_file, bucket, temp_dir)
                
                # Submit all tasks
                future_to_row = {executor.submit(process_func, row): row for row in rows}
                
                # Process results as they complete
                for future in as_completed(future_to_row):
                    success, old_name, error_msg = future.result()
                    update_progress(success, old_name, error_msg)
            
            progress_bar.close()
            
            # Report results
            if errors:
                print(f"\nCompleted with {len(errors)} errors out of {total_files} files")
                print("Check b2_rename_errors.log for details")
            else:
                print(f"\nSuccessfully processed all {total_files} files!")
    
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='B2 File Rename and Reupload Tool')
    parser.add_argument('--mapping-file', default='b2_supabase_faiss_mapping.csv',
                      help='Path to the mapping file (default: b2_supabase_faiss_mapping.csv)')
    parser.add_argument('--max-workers', type=int, default=10,
                      help='Number of parallel workers (default: 10)')
    parser.add_argument('--generate-mapping', action='store_true',
                      help='Generate new mapping file from bucket contents')
    parser.add_argument('--batch-size', type=int, default=100,
                      help='Batch size for processing (default: 100)')
    
    args = parser.parse_args()
    
    # Run the process with command line arguments
    process_files_in_batches(
        mapping_path=args.mapping_file,
        batch_size=args.batch_size,
        generate_mapping=args.generate_mapping,
        max_workers=args.max_workers
    )
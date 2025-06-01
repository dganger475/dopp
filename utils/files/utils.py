"""
File Utilities
==============

Provides helper functions for file operations, validation, and management.
"""

import os
import re
from typing import Optional
import time
from functools import wraps
from b2sdk.v2 import B2Api, InMemoryAccountInfo
from b2sdk.v2.exception import B2Error

def allowed_file(filename):
    """Check if file has an allowed extension."""
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_face_filename(face_id: int) -> str:
    """
    Generate an anonymized filename for a face image.
    
    Args:
        face_id: The ID of the face in the database
        
    Returns:
        str: Filename in format 'face_000123.jpg'
    """
    return f"face_{face_id:06d}.jpg"

def parse_face_id_from_filename(filename: str) -> Optional[int]:
    """
    Extract the face ID from an anonymized filename.
    
    Args:
        filename: The filename to parse (e.g., 'face_000123.jpg')
        
    Returns:
        int: The face ID if valid, None otherwise
    """
    match = re.match(r'face_(\d{6})\.jpg$', filename)
    if match:
        return int(match.group(1))
    return None

def is_anonymized_face_filename(filename: str) -> bool:
    """
    Check if a filename follows the anonymized face format.
    
    Args:
        filename: The filename to check
        
    Returns:
        bool: True if the filename matches the format 'face_000123.jpg'
    """
    return bool(re.match(r'face_\d{6}\.jpg$', filename))

def rate_limit(max_retries=3, delay=1):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except B2Error as e:
                    if "download_cap_exceeded" in str(e):
                        retries += 1
                        if retries == max_retries:
                            raise
                        time.sleep(delay * retries)  # Exponential backoff
                    else:
                        raise
            return None
        return wrapper
    return decorator

@rate_limit(max_retries=3, delay=2)
def download_file(bucket, file_name):
    """Download a file from B2 with rate limiting."""
    try:
        file_info = bucket.get_file_info_by_name(file_name)
        if not file_info:
            return None
        
        # Download with retry logic
        download = bucket.download_file_by_name(file_name)
        return download
    except B2Error as e:
        if "download_cap_exceeded" in str(e):
            raise  # Let the decorator handle the retry
        raise

def get_b2_bucket():
    """Get B2 bucket with proper configuration."""
    info = InMemoryAccountInfo()
    b2_api = B2Api(info)
    
    # Use environment variables for credentials
    application_key_id = os.getenv('B2_APPLICATION_KEY_ID')
    application_key = os.getenv('B2_APPLICATION_KEY')
    bucket_name = os.getenv('B2_BUCKET_NAME')
    
    b2_api.authorize_account("production", application_key_id, application_key)
    return b2_api.get_bucket_by_name(bucket_name)

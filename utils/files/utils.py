"""
File Utilities
==============

Provides helper functions for file operations, validation, and management.
"""

import os
import re
from typing import Optional

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

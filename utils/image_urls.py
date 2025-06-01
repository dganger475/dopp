"""
Image URL utilities for handling B2 image URLs.
"""

from flask import current_app
from utils.db.storage import get_storage
from utils.files.utils import is_anonymized_face_filename
import logging

logger = logging.getLogger(__name__)

def get_face_image_url(filename: str) -> str:
    """
    Get the URL for a face image.
    
    Args:
        filename: The face image filename
        
    Returns:
        str: The URL for the image
    """
    try:
        if not filename:
            return current_app.config.get('DEFAULT_FACE_IMAGE', '/static/default_face.jpg')
            
        # Verify it's an anonymized filename
        if not is_anonymized_face_filename(filename):
            logger.warning(f"Invalid face filename format: {filename}")
            return current_app.config.get('DEFAULT_FACE_IMAGE', '/static/default_face.jpg')
            
        # Get URL from storage backend
        storage = get_storage()
        return storage.get_url(filename, folder='faces')
        
    except Exception as e:
        logger.error(f"Error getting face image URL: {str(e)}")
        return current_app.config.get('DEFAULT_FACE_IMAGE', '/static/default_face.jpg')

def get_profile_image_url(filename: str) -> str:
    """
    Get the URL for a profile image.
    
    Args:
        filename: The profile image filename
        
    Returns:
        str: The URL for the image
    """
    try:
        if not filename:
            return current_app.config.get('DEFAULT_PROFILE_IMAGE', '/static/default_profile.jpg')
            
        # Get URL from storage backend
        storage = get_storage()
        return storage.get_url(filename, folder='profile_pics')
        
    except Exception as e:
        logger.error(f"Error getting profile image URL: {str(e)}")
        return current_app.config.get('DEFAULT_PROFILE_IMAGE', '/static/default_profile.jpg') 
"""
All image path logic (profile, face, etc.) must use these utilities for consistency and to avoid 404s.
"""

import os
from flask import current_app, url_for
import logging
import urllib.parse

logger = logging.getLogger(__name__)

def normalize_profile_image_path(path):
    """Flexible lookup: Try /static/profile_pics/, /static/images/, fallback to /static/default_profile.png"""
    if not path:
        return "/static/images/default_profile.png"
        
    # If it's already a full URL or starts with /static/, return as is
    if path.startswith(('http://', 'https://', '/static/')):
        return path
        
    # Extract filename from path
    filename = path.split('/')[-1]
    
    # Check in profile_pics directory first
    img_path = os.path.join(current_app.root_path, "static", "profile_pics", filename)
    if os.path.exists(img_path):
        resolved = "/static/profile_pics/" + filename
        current_app.logger.debug(
            f"[normalize_profile_image_path] Found in profile_pics: {resolved}"
        )
        return resolved.replace("\\", "/")
        
    # Check in faces directory
    img_path = os.path.join(current_app.root_path, "static", "faces", filename)
    if os.path.exists(img_path):
        resolved = "/static/faces/" + filename
        current_app.logger.debug(
            f"[normalize_profile_image_path] Found in faces: {resolved}"
        )
        return resolved.replace("\\", "/")
        
    # Check in images directory
    img_path = os.path.join(current_app.root_path, "static", "images", filename)
    if os.path.exists(img_path):
        resolved = "/static/images/" + filename
        current_app.logger.debug(
            f"[normalize_profile_image_path] Found in images: {resolved}"
        )
        return resolved.replace("\\", "/")
        
    # Check if this is being called from the search context
    import inspect
    stack = inspect.stack()
    caller_file = stack[1].filename if len(stack) > 1 else ''
    is_search_context = 'search.py' in caller_file
    
    if is_search_context:
        # For search page, don't return default images as they can't be used for face recognition
        current_app.logger.warning(
            f"[normalize_profile_image_path] Path '{path}' not found in search context. Returning None."
        )
        return None
    else:
        # For non-search contexts, return fallback default image
        fallback = "/static/images/default_profile.png"
        
        # Check if we have a default-profile.png in images folder
        if os.path.exists(os.path.join(current_app.root_path, "static", "images", "default-profile.png")):
            fallback = "/static/images/default-profile.png"
        
        current_app.logger.warning(
            f"[normalize_profile_image_path] Path '{path}' not found. Fallback to: {fallback}"
        )
        return fallback.replace("\\", "/")

def get_image_path(filename, subfolder=''):
    """
    Helper function to locate an image file in multiple possible locations.
    
    Args:
        filename (str): The name of the image file to find
        subfolder (str): Optional subfolder to check within each directory
        
    Returns:
        str: URL to the image if found, or URL to default image if not found
    """
    if not filename:
        return url_for('static', filename='default_profile.png')
    
    # List of possible directories to check (in order of priority)
    possible_dirs = [
        os.path.join('profile_pics', subfolder).replace('\\', '/'),
        os.path.join('images', subfolder).replace('\\', '/'),
        os.path.join('faces', subfolder).replace('\\', '/'),
        'profile_pics',
        'images',
        'faces',
        ''  # Check in static root as last resort
    ]
    
    # Remove empty strings and duplicates while preserving order
    possible_dirs = list(dict.fromkeys(d for d in possible_dirs if d.strip()))
    
    # Check if file exists in any of the possible directories
    for directory in possible_dirs:
        # Skip empty directory names
        if not directory:
            path = filename
        else:
            path = os.path.join(directory, filename).replace('\\', '/')
            
        full_path = os.path.join(current_app.static_folder, path)
        
        # Check if file exists and is a file (not a directory)
        if os.path.isfile(full_path):
            # Return URL path with proper formatting
            return url_for('static', filename=path)
    
    # Log the missing file for debugging
    logger.warning(f"Image not found: {filename} in subfolder: {subfolder}")
    
    # Return default image if not found
    return url_for('static', filename='default_profile.png')

def normalize_extracted_face_path(filename):
    """
    Normalize the path for extracted face images.
    
    Args:
        filename (str): The name of the face image file to find
        
    Returns:
        str: URL to the face image if found, or URL to default image if not found
    """
    import urllib.parse
    if not filename or not isinstance(filename, str):
        current_app.logger.warning(
            "[normalize_extracted_face_path] No filename provided or invalid filename type, using default profile image."
        )
        return url_for('static', filename='default_profile.png')
    # Decode twice to handle double-encoded filenames
    decoded_filename = urllib.parse.unquote(urllib.parse.unquote(filename))
    basename = os.path.basename(decoded_filename)
    encoded_filename = urllib.parse.quote(basename, safe='')
    extracted_faces_path = os.path.join(current_app.root_path, 'static', 'extracted_faces', basename)
    if os.path.exists(extracted_faces_path):
        return url_for('static', filename=f'extracted_faces/{encoded_filename}')
    faces_path = os.path.join(current_app.root_path, 'static', 'faces', basename)
    if os.path.exists(faces_path):
        return url_for('static', filename=f'faces/{encoded_filename}')
    static_path = os.path.join(current_app.root_path, 'static', basename)
    if os.path.exists(static_path):
        return url_for('static', filename=encoded_filename)
    current_app.logger.warning(f"Face image not found: {basename}")
    return url_for('static', filename='default_profile.png')

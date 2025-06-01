"""
All image path logic (profile, face, etc.) must use these utilities for consistency and to avoid 404s.
"""

import os
from flask import current_app, url_for


def normalize_profile_image_path(path):
    """Flexible lookup: Try /static/profile_pics/, /static/images/, fallback to /static/default_profile.png"""
    if not path:
        # Consider using: url_for('static', filename='images/default-profile.png')
        resolved = (
            "/static/images/default-profile.png"
            if os.path.exists(
                os.path.join(
                    current_app.root_path, "static", "images", "default-profile.png"
                )
            )
            else "/static/default_profile.png"
        )
        current_app.logger.debug(
            f"[normalize_profile_image_path] No path provided, resolved to default: {resolved}"
        )
        return resolved
    # If already a full URL or static path, return as is
    if path.startswith(("http://", "https://")) or path.startswith("/static/"):
        current_app.logger.debug(
            f"[normalize_profile_image_path] Path already URL/static: {path}"
        )
        # Normalize to forward slashes for web
        return path.replace("\\", "/")
    # Remove any duplicate or incorrect prefixes
    filename = path.split("/")[-1]
    # Try profile_pics
    pic_path = os.path.join(current_app.root_path, "static", "profile_pics", filename)
    if os.path.exists(pic_path):
        # Consider using: url_for('static', filename=f'profile_pics/{filename}')
        resolved = "/static/profile_pics/" + filename
        current_app.logger.debug(
            f"[normalize_profile_image_path] Found in profile_pics: {resolved}"
        )
        return resolved.replace("\\", "/")
    # Try images
    img_path = os.path.join(current_app.root_path, "static", "images", filename)
    if os.path.exists(img_path):
        # Consider using: url_for('static', filename=f'images/{filename}')
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
        fallback = "/static/default_profile.png"
        
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
        os.path.join('extracted_faces', subfolder).replace('\\', '/'),
        os.path.join('faces', subfolder).replace('\\', '/'),
        os.path.join('profile_pics', subfolder).replace('\\', '/'),
        'extracted_faces',
        'faces',
        'profile_pics',
    ]
    
    # Check if file exists in any of the possible directories
    for directory in possible_dirs:
        path = os.path.join(directory, filename).replace('\\', '/')
        full_path = os.path.join(current_app.static_folder, path)
        if os.path.exists(full_path):
            return url_for('static', filename=path)
    
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
    if not filename or not isinstance(filename, str):
        current_app.logger.warning(
            "[normalize_extracted_face_path] No filename provided or invalid filename type, using default profile image."
        )
        return url_for('static', filename='default_profile.png')
    
    # Remove any leading slashes or directory traversal attempts
    filename = os.path.basename(filename)
    
    # Check the primary location first: static/extracted_faces/
    extracted_faces_path = os.path.join(current_app.root_path, 'static', 'extracted_faces', filename)
    if os.path.exists(extracted_faces_path):
        return url_for('static', filename=f'extracted_faces/{filename}')
    
    # If not found, try faces/ as an alternative location
    faces_path = os.path.join(current_app.root_path, 'static', 'faces', filename)
    if os.path.exists(faces_path):
        return url_for('static', filename=f'faces/{filename}')
    
    # If still not found, try the filename directly in the static folder
    static_path = os.path.join(current_app.root_path, 'static', filename)
    if os.path.exists(static_path):
        return url_for('static', filename=filename)
    
    # Log the missing file
    current_app.logger.warning(f"Face image not found: {filename}")
    return url_for('static', filename='default_profile.png')

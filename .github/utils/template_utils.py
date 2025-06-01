import os
from flask import current_app

def get_image_path(filename, subfolder=''):
    """
    Helper function to locate an image file in multiple possible locations.
    
    Args:
        filename (str): The name of the image file to find
        subfolder (str): Optional subfolder to check within each directory
        
    Returns:
        str: Relative path to the image if found, or path to default image if not found
    """
    if not filename:
        return f"{current_app.static_url_path}/default_profile.png"
    
    # List of possible directories to check (in order of priority)
    possible_dirs = [
        os.path.join('profile_pics', subfolder).replace('\\', '/'),
        os.path.join('faces', subfolder).replace('\\', '/'),
        os.path.join('extracted_faces', subfolder).replace('\\', '/'),
        'profile_pics',
        'faces',
        'extracted_faces',
        '',  # Check in static root as last resort
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
            return f"{current_app.static_url_path}/{path}"
    
    # Log the missing file for debugging
    current_app.logger.warning(f"Image not found: {filename} in subfolder: {subfolder}")
    
    # Return default image if not found
    return f"{current_app.static_url_path}/default_profile.png"

"""Application configuration settings."""

import os

# File storage settings
UPLOAD_FOLDER = 'static/uploads'
PROFILE_IMAGES_FOLDER = 'static/profile_images'
COVER_IMAGES_FOLDER = 'static/cover_images'
FACES_FOLDER = 'static/faces'
EXTRACTED_FACES_FOLDER = 'static/extracted_faces'
USER_FACES_FOLDER = 'static/user_faces'

# Allowed image extensions
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}

# Image processing settings
MAX_IMAGE_SIZE = (800, 800)  # Maximum image dimensions
DEFAULT_FACE_PADDING = 0.3  # 30% padding around faces

# Database settings
DATABASE_PATH = 'faces.db'
USERS_DATABASE_PATH = 'users.db'

# Face matching settings
FAISS_INDEX_PATH = 'faces.index' 
FILENAMES_PICKLE_PATH = 'faces_filenames.pkl'
DEFAULT_MATCH_LIMIT = 20

# Feature flags
ENABLE_FAISS = True  # Whether to use FAISS for similarity search
ENABLE_FACE_RECOGNITION = True  # Whether to use face recognition

# Social feature settings
DEFAULT_BIO = "No bio added yet."
DEFAULT_PROFILE_IMAGE = '/static/default_profile.png'
DEFAULT_COVER_IMAGE = '/static/default_cover.png'

def get_absolute_path(relative_path):
    """
    Get absolute path from a path relative to the app's root directory.
    
    Args:
        relative_path: Path relative to the app's root directory
        
    Returns:
        Absolute path
    """
    from flask import current_app
    return os.path.join(current_app.root_path, relative_path)

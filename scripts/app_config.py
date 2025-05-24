"""
Centralized configuration for utility scripts.
This ensures all scripts use the same paths as the main application.
"""
import os

# Get the project root directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

# Data directories
DATA_ROOT = os.path.join(PROJECT_ROOT, 'data')
DB_DIR = os.path.join(DATA_ROOT, 'db')
INDEX_DIR = os.path.join(DATA_ROOT, 'index')

# Database paths
DB_PATH = os.environ.get('DB_PATH', os.path.join(DB_DIR, 'faces.db'))

# Face recognition paths
INDEX_PATH = os.environ.get('INDEX_PATH', os.path.join(INDEX_DIR, 'faces.index'))
MAP_PATH = os.environ.get('MAP_PATH', os.path.join(INDEX_DIR, 'faces_filenames.pkl'))

# Static directories
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'static')
UPLOAD_FOLDER = os.path.join(STATIC_ROOT, 'uploads')
EXTRACTED_FACES = os.path.join(STATIC_ROOT, 'extracted_faces')
PROFILE_PICS = os.path.join(STATIC_ROOT, 'profile_pics')
COVER_PICS = os.path.join(STATIC_ROOT, 'covers')
SORTED_FACES = os.path.join(STATIC_ROOT, 'sorted_faces')

# Ensure all directories exist
for directory in [DB_DIR, INDEX_DIR, UPLOAD_FOLDER, EXTRACTED_FACES, 
                 PROFILE_PICS, COVER_PICS, SORTED_FACES]:
    os.makedirs(directory, exist_ok=True) 
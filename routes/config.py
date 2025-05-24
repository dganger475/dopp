"""
Routes Configuration Module
=========================

This module provides centralized configuration for all routes,
ensuring consistent path handling and configuration access.
"""

from flask import current_app
import os

def get_image_paths(filename):
    """
    Get all possible paths for an image file.
    Returns a list of paths in order of preference.
    """
    if not filename:
        return []
        
    paths = []
    
    # First try the configured paths from app config
    if current_app.config.get('EXTRACTED_FACES'):
        paths.append(os.path.join(current_app.config['EXTRACTED_FACES'], filename))
    
    # Then try static directories
    static_paths = [
        os.path.join('static', 'extracted_faces', filename),
        os.path.join('static', 'faces', filename),
        os.path.join('extracted_faces', filename),
        os.path.join('faces', filename)
    ]
    
    for path in static_paths:
        full_path = os.path.join(current_app.root_path, path)
        paths.append(full_path)
    
    return paths

def get_profile_image_path(filename):
    """Get the full path for a profile image."""
    if not filename:
        return get_default_profile_image_path()
        
    # Try configured path first
    if current_app.config.get('PROFILE_PICS'):
        path = os.path.join(current_app.config['PROFILE_PICS'], filename)
        if os.path.exists(path):
            return path
    
    # Fallback to static directory
    path = os.path.join(current_app.root_path, 'static', 'profile_pics', filename)
    if os.path.exists(path):
        return path
        
    return get_default_profile_image_path()

def get_default_profile_image_path():
    """Get the path to the default profile image."""
    if current_app.config.get('DEFAULT_PROFILE_IMAGE'):
        path = current_app.config['DEFAULT_PROFILE_IMAGE']
        if os.path.exists(path):
            return path
    
    return os.path.join(current_app.root_path, 'static', 'default_profile.png')

def get_db_path():
    """Get the database path from configuration."""
    if current_app.config.get('DB_PATH'):
        return current_app.config['DB_PATH']
    return os.path.join(current_app.root_path, 'faces.db')

def get_index_path():
    """Get the FAISS index path from configuration."""
    if current_app.config.get('INDEX_PATH'):
        return current_app.config['INDEX_PATH']
    return os.path.join(current_app.root_path, 'faces.index')

def get_map_path():
    """Get the filename mapping path from configuration."""
    if current_app.config.get('MAP_PATH'):
        return current_app.config['MAP_PATH']
    return os.path.join(current_app.root_path, 'faces_filenames.pkl') 
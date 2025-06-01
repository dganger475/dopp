"""
Face Detection Utilities for DoppleGanger
=======================================

Provides functions for detecting faces in images using face_recognition.
"""

import logging
import face_recognition
from typing import List, Tuple, Optional
import numpy as np

logger = logging.getLogger(__name__)

def detect_faces(image_path: str) -> List[Tuple[int, int, int, int]]:
    """
    Detect faces in an image and return their locations.
    
    Args:
        image_path (str): Path to the image file
        
    Returns:
        List[Tuple[int, int, int, int]]: List of face locations (top, right, bottom, left)
    """
    try:
        # Load image
        image = face_recognition.load_image_file(image_path)
        
        # Detect faces
        face_locations = face_recognition.face_locations(image)
        
        if not face_locations:
            logger.warning(f"No faces detected in image: {image_path}")
            return []
            
        logger.info(f"Detected {len(face_locations)} faces in image: {image_path}")
        return face_locations
        
    except Exception as e:
        logger.error(f"Error detecting faces in {image_path}: {e}")
        return []

def get_largest_face(face_locations: List[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    """
    Get the largest face from a list of face locations.
    
    Args:
        face_locations (List[Tuple[int, int, int, int]]): List of face locations
        
    Returns:
        Optional[Tuple[int, int, int, int]]: Location of the largest face, or None if no faces
    """
    if not face_locations:
        return None
        
    # Calculate areas of all faces
    areas = [(bottom - top) * (right - left) for top, right, bottom, left in face_locations]
    
    # Get index of largest face
    largest_idx = np.argmax(areas)
    
    return face_locations[largest_idx] 
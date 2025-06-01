"""
Face Recognizer Module
=======================

Provides a class-based interface for face recognition operations.
Wraps the existing face recognition functions in a more object-oriented way.
"""

import logging
from typing import Optional, List, Dict, Any
import numpy as np
from PIL import Image

from .recognition import (
    extract_face_encoding,
    find_similar_faces,
    find_similar_faces_faiss,
    rebuild_faiss_index,
    calculate_similarity,
    format_similarity,
    get_real_image_path
)

logger = logging.getLogger(__name__)

class FaceRecognizer:
    """A class to handle face recognition operations."""
    
    def __init__(self, app=None):
        """Initialize the FaceRecognizer.
        
        Args:
            app: Optional Flask application instance
        """
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        # Any additional initialization can go here
    
    def extract_encoding(self, image_path: str) -> Optional[np.ndarray]:
        """Extract face encoding from an image.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Face encoding as a numpy array, or None if no face found
        """
        return extract_face_encoding(image_path)
    
    def find_similar(
        self, 
        encoding: np.ndarray, 
        top_k: int = 50,
        use_faiss: bool = True
    ) -> List[Dict[str, Any]]:
        """Find similar faces to the given encoding.
        
        Args:
            encoding: Face encoding to search for
            top_k: Maximum number of results to return
            use_faiss: Whether to use FAISS for search (faster for large datasets)
            
        Returns:
            List of dictionaries with match information
        """
        if use_faiss:
            return find_similar_faces_faiss(encoding, top_k=top_k)
        return find_similar_faces(encoding, top_k=top_k)
    
    def rebuild_index(self) -> bool:
        """Rebuild the FAISS index.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            rebuild_faiss_index(self.app)
            return True
        except Exception as e:
            logger.error(f"Error rebuilding FAISS index: {e}")
            return False
    
    @staticmethod
    def calculate_similarity_score(distance: float, threshold: float = 0.6) -> float:
        """Calculate similarity percentage from a distance.
        
        Args:
            distance: L2 distance between face encodings
            threshold: Distance threshold (default 0.6)
            
        Returns:
            Similarity percentage (0-100)
        """
        return calculate_similarity(distance, threshold)
    
    @staticmethod
    def format_similarity_score(similarity: float) -> str:
        """Format a similarity score as a percentage string.
        
        Args:
            similarity: Similarity score (0-100)
            
        Returns:
            Formatted string (e.g., "95.25%")
        """
        return format_similarity(similarity)
    
    def get_image_path(self, image_path: str) -> str:
        """Get the real path of an image, handling any necessary transformations.
        
        Args:
            image_path: Original image path
            
        Returns:
            Resolved image path
        """
        return get_real_image_path(image_path)

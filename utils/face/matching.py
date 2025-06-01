import faiss
import numpy as np
from typing import List, Tuple
from models.face import Face
from utils.files.utils import parse_face_id_from_filename
import logging

logger = logging.getLogger(__name__)

def find_matches(face_encoding: np.ndarray, index: faiss.Index, filenames: List[str], k: int = 5) -> List[Tuple[str, float]]:
    """
    Find matches for a face encoding using FAISS.
    
    Args:
        face_encoding: The face encoding to match
        index: The FAISS index
        filenames: List of filenames corresponding to the index
        k: Number of matches to return
        
    Returns:
        List of (filename, distance) tuples
    """
    try:
        # Reshape encoding for FAISS
        face_encoding = face_encoding.reshape(1, -1).astype('float32')
        
        # Search the index
        distances, indices = index.search(face_encoding, k)
        
        # Convert results to list of (filename, distance) tuples
        matches = []
        for i, idx in enumerate(indices[0]):
            if idx < len(filenames):
                filename = filenames[idx]
                # Verify the filename is in the new format
                if parse_face_id_from_filename(filename):
                    matches.append((filename, float(distances[0][i])))
        
        return matches
        
    except Exception as e:
        logger.error(f"Error finding matches: {str(e)}")
        return []

def get_face_details(matches: List[Tuple[str, float]]) -> List[dict]:
    """
    Get details for matched faces from the database.
    
    Args:
        matches: List of (filename, distance) tuples
        
    Returns:
        List of face details dictionaries
    """
    try:
        face_details = []
        for filename, distance in matches:
            face_id = parse_face_id_from_filename(filename)
            if face_id:
                face = Face.get_by_id(face_id)
                if face:
                    face_details.append({
                        'id': face.id,
                        'filename': face.filename,
                        'year': face.year,
                        'state': face.state,
                        'school': face.school,
                        'page': face.page,
                        'distance': distance
                    })
        return face_details
        
    except Exception as e:
        logger.error(f"Error getting face details: {str(e)}")
        return [] 
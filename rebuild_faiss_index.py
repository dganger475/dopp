"""
FAISS Index Rebuild Script
=========================

This script rebuilds the FAISS index for face images after renaming.
"""

import os
import logging
import numpy as np
import face_recognition
from pathlib import Path
import faiss
from tqdm import tqdm
import re
import csv
import pandas as pd
import shutil
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def backup_file(filepath):
    """Create a backup of a file with timestamp."""
    if os.path.exists(filepath):
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = f"{filepath}.backup_{timestamp}"
        shutil.copy2(filepath, backup_path)
        logger.info(f"Created backup: {backup_path}")
        return backup_path
    return None

def load_mapping_file(mapping_path='b2_supabase_faiss_mapping.csv'):
    """Load the mapping file and create a lookup dictionary."""
    try:
        df = pd.read_csv(mapping_path)
        # Create a mapping from new filename to old filename
        return dict(zip(df['new_filename'], df['old_filename']))
    except Exception as e:
        logger.error(f"Error loading mapping file: {e}")
        return {}

def is_excluded_face(filename, mapping):
    """Check if the face should be excluded (Texas or Illinois)."""
    # Get the original filename from the mapping
    original_filename = mapping.get(filename, filename)
    
    # Patterns for Texas and Illinois faces
    excluded_patterns = [
        r'texas',
        r'il_',
        r'illinois',
        r'_il_',
        r'_tx_',
        r'_texas_'
    ]
    
    original_filename_lower = original_filename.lower()
    return any(re.search(pattern, original_filename_lower) for pattern in excluded_patterns)

def load_face_encodings(image_path):
    """Load face encodings from an image."""
    try:
        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)
        
        if not face_locations:
            logger.warning(f"No faces found in {image_path}")
            return None
            
        # Get the largest face
        face_areas = [(bottom - top) * (right - left) for top, right, bottom, left in face_locations]
        largest_face_idx = np.argmax(face_areas)
        face_location = face_locations[largest_face_idx]
        
        # Get face encoding
        face_encoding = face_recognition.face_encodings(image, [face_location])[0]
        return face_encoding
        
    except Exception as e:
        logger.error(f"Error processing {image_path}: {e}")
        return None

def rebuild_faiss_index(faces_dir="static/extracted_faces", index_path="faces.index"):
    """Rebuild the FAISS index for face images."""
    try:
        # Backup existing files
        backup_file(index_path)
        backup_file('face_filenames.npy')
        
        # Load the mapping file
        mapping = load_mapping_file()
        if not mapping:
            logger.error("Failed to load mapping file")
            return False
            
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png'}
        image_files = [
            f for f in Path(faces_dir).glob('*')
            if f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            logger.error(f"No image files found in {faces_dir}")
            return False
            
        logger.info(f"Found {len(image_files)} total images")
        
        # Filter out excluded faces
        image_files = [f for f in image_files if not is_excluded_face(f.name, mapping)]
        logger.info(f"After filtering Texas/Illinois: {len(image_files)} images")
        
        # Load face encodings
        face_encodings = []
        valid_filenames = []
        excluded_count = 0
        
        for image_file in tqdm(image_files, desc="Processing faces"):
            if is_excluded_face(image_file.name, mapping):
                excluded_count += 1
                continue
                
            face_encoding = load_face_encodings(str(image_file))
            if face_encoding is not None:
                face_encodings.append(face_encoding)
                valid_filenames.append(image_file.name)
        
        if not face_encodings:
            logger.error("No valid face encodings found")
            return False
            
        # Convert to numpy array
        face_encodings = np.array(face_encodings).astype('float32')
        
        # Create FAISS index
        dimension = face_encodings.shape[1]  # Should be 128 for face_recognition
        index = faiss.IndexFlatL2(dimension)
        
        # Add vectors to index
        index.add(face_encodings)
        
        # Save index and filenames
        faiss.write_index(index, index_path)
        np.save('face_filenames.npy', valid_filenames)
        
        logger.info(f"Successfully rebuilt FAISS index with {len(valid_filenames)} faces")
        logger.info(f"Excluded {excluded_count} Texas/Illinois faces")
        return True
        
    except Exception as e:
        logger.error(f"Error rebuilding FAISS index: {e}")
        return False

if __name__ == "__main__":
    rebuild_faiss_index()

#!/usr/bin/env python
"""
Prepare model files for deployment by moving them to a dedicated models directory.
This script helps organize large model files for Docker volume mounting.
"""

import logging
import os
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# List of model files to move
MODEL_FILES = [
    "face_quality_classifier.h5",
    "GFPGANv1.4.pth",
    "RealESRGAN_x4plus_anime_6B.pth",
    "ESPCN_x4.pb",
    "CodeFormer.pth"
]

# List of data files to move
DATA_FILES = [
    "faces.db",
    "users.db",
    "faces.index",
    "faces_filenames.pkl"
]

def create_directory(directory):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")

def move_file(src, dest):
    """Move file from source to destination."""
    if os.path.exists(src):
        # Create destination directory if it doesn't exist
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        
        # If destination already exists, don't overwrite
        if os.path.exists(dest):
            logger.info(f"File already exists at {dest}, skipping")
            return False
            
        # Move the file
        shutil.copy2(src, dest)
        logger.info(f"Copied {src} to {dest}")
        return True
    else:
        logger.warning(f"Source file {src} does not exist")
        return False

def main():
    """Main function to prepare model files."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent.absolute()
    
    # Create models and data directories
    models_dir = os.path.join(project_root, "models")
    data_dir = os.path.join(project_root, "data")
    
    create_directory(models_dir)
    create_directory(data_dir)
    
    # Move model files
    for model_file in MODEL_FILES:
        src = os.path.join(project_root, model_file)
        dest = os.path.join(models_dir, model_file)
        move_file(src, dest)
    
    # Move data files
    for data_file in DATA_FILES:
        src = os.path.join(project_root, data_file)
        dest = os.path.join(data_dir, data_file)
        move_file(src, dest)
    
    logger.info("Model and data files prepared for deployment")

if __name__ == "__main__":
    main()

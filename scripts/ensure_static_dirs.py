"""
Script to ensure all required static directories exist and have proper permissions.
"""

import os
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def ensure_static_dirs():
    """Ensure all required static directories exist."""
    # Get the project root directory
    project_root = Path(__file__).parent.parent
    
    # List of required static directories
    static_dirs = [
        'static',
        'static/profile_pics',
        'static/images',
        'static/faces',
        'static/extracted_faces'
    ]
    
    # Create each directory if it doesn't exist
    for dir_path in static_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory exists: {full_path}")
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
    
    # Create default profile image if it doesn't exist
    default_image_path = project_root / 'static' / 'default_profile.png'
    if not default_image_path.exists():
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a blank image with blue background
            img = Image.new("RGB", (200, 200), color=(78, 115, 223))
            d = ImageDraw.Draw(img)
            
            # Try to add a question mark
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except IOError:
                font = ImageFont.load_default()
            
            # Draw a question mark in the center
            d.text((100, 100), "?", fill="white", font=font, anchor="mm")
            
            # Save the image
            img.save(default_image_path)
            logger.info(f"Created default profile image at {default_image_path}")
        except Exception as e:
            logger.error(f"Failed to create default profile image: {e}")

if __name__ == "__main__":
    ensure_static_dirs() 
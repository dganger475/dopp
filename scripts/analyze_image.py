import io

import face_recognition
from PIL import Image

import numpy as np


def analyze_single_image(image_path):
    """Calculate and display detailed quality score for a single image."""
    # Open and convert image
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    
    # Size score (0.4 weight)
    width, height = img.size
    size_score = min(width, height) / 300.0
    
    # Convert to numpy array
    img_array = np.array(img)
    
    # Contrast score (0.3 weight)
    contrast = np.std(img_array)
    contrast_score = min(contrast / 50.0, 1.0)
    
    # Face detection confidence
    face_locations = face_recognition.face_locations(img_array)
    face_detected = len(face_locations) > 0
    
    # Sharpness score (0.3 weight)
    gray = np.mean(img_array, axis=2)
    laplacian = np.var(gray)
    sharpness_score = min(laplacian / 500.0, 1.0)
    
    # Calculate final weighted score
    final_score = (size_score * 0.4 + contrast_score * 0.3 + sharpness_score * 0.3)
    
    print("\nIMAGE QUALITY ANALYSIS")
    print("=" * 50)
    print(f"Image dimensions: {width}x{height}")
    print(f"Size score: {size_score:.3f} (40% weight)")
    print(f"Contrast score: {contrast_score:.3f} (30% weight)")
    print(f"Sharpness score: {sharpness_score:.3f} (30% weight)")
    print(f"Face detected: {'Yes' if face_detected else 'No'}")
    print("=" * 50)
    print(f"Final quality score: {final_score:.3f}")
    
    return final_score 
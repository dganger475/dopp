import logging
import os
import sqlite3

import face_recognition
from PIL import Image

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_image_quality_score(image_path):
    """Calculate quality score based on multiple factors."""
    try:
        # Open image
        img = Image.open(image_path)
        
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Get image dimensions
        width, height = img.size
        
        # Calculate basic metrics
        size_score = min(width, height) / 300.0  # Normalize to desired size
        
        # Convert to numpy array for further analysis
        img_array = np.array(img)
        
        # Calculate contrast
        contrast = np.std(img_array)
        contrast_score = min(contrast / 50.0, 1.0)  # Normalize contrast
        
        # Check face detection confidence
        face_locations = face_recognition.face_locations(img_array)
        if not face_locations:
            return 0.0  # No face detected
        
        # Calculate sharpness using variance of Laplacian
        gray = np.mean(img_array, axis=2)
        laplacian = np.var(gray)
        sharpness_score = min(laplacian / 500.0, 1.0)  # Normalize sharpness
        
        # Combine scores (weighted average)
        final_score = (size_score * 0.4 + contrast_score * 0.3 + sharpness_score * 0.3)
        
        return final_score
        
    except Exception as e:
        logging.error(f"Error analyzing image {image_path}: {e}")
        return 0.0

def cleanup_low_quality_images(quality_threshold=0.5):
    """Remove images that don't meet the quality threshold."""
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    
    deleted_count = 0
    processed_count = 0
    
    try:
        cursor.execute("SELECT id, filename, image_path FROM faces")
        faces = cursor.fetchall()
        total_faces = len(faces)
        
        print(f"\nAnalyzing {total_faces} faces...")
        
        for face_id, filename, image_path in faces:
            processed_count += 1
            
            if processed_count % 100 == 0:
                print(f"Processed {processed_count}/{total_faces} faces...")
            
            if not os.path.exists(image_path):
                continue
                
            quality_score = get_image_quality_score(image_path)
            
            if quality_score < quality_threshold:
                try:
                    # Delete from database
                    cursor.execute("DELETE FROM faces WHERE id = ?", (face_id,))
                    
                    # Delete file
                    os.remove(image_path)
                    
                    deleted_count += 1
                    logging.info(f"Deleted low quality face: {filename} (Score: {quality_score:.2f})")
                    
                except Exception as e:
                    logging.error(f"Error deleting {filename}: {e}")
        
        conn.commit()
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()
    
    return deleted_count, total_faces

if __name__ == "__main__":
    print("\nThis script will analyze and remove low-quality face images.")
    print("Quality is determined by size, contrast, sharpness, and face detection confidence.")
    
    threshold = float(input("\nEnter quality threshold (0.0-1.0, recommended 0.5): "))
    confirmation = input("\nAre you sure you want to proceed? (yes/no): ")
    
    if confirmation.lower() == 'yes':
        deleted, total = cleanup_low_quality_images(threshold)
        
        conn = sqlite3.connect("faces.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM faces")
        remaining = cursor.fetchone()[0]
        conn.close()
        
        print(f"\nProcessing complete:")
        print(f"- Total faces analyzed: {total}")
        print(f"- Low quality faces removed: {deleted}")
        print(f"- Remaining faces in database: {remaining}")
    else:
        print("\nCleanup cancelled.") 
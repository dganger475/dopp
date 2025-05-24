import logging
import os
import sqlite3

import cv2
import face_recognition
from PIL import Image
from tqdm import tqdm

import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def get_quality_score(image_path):
    """Calculate quality score for an image."""
    try:
        # Open image
        img = Image.open(image_path)
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Size score (0.3 weight)
        width, height = img.size
        size_score = min((width * height) / (300 * 300), 1.0)
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Contrast score (0.3 weight)
        luminance = 0.299 * img_array[:,:,0] + 0.587 * img_array[:,:,1] + 0.114 * img_array[:,:,2]
        contrast = np.std(luminance)
        contrast_score = min(contrast / 70.0, 1.0)  # Adjusted threshold
        
        # Sharpness score (0.4 weight)
        laplacian = cv2.Laplacian(luminance.astype(np.uint8), cv2.CV_64F)
        sharpness = np.var(laplacian)
        sharpness_score = min(sharpness / 1000.0, 1.0)  # Adjusted threshold
        
        # Calculate final weighted score
        final_score = (
            size_score * 0.3 +
            contrast_score * 0.3 +
            sharpness_score * 0.4
        )
        
        return final_score
        
    except Exception as e:
        logging.error(f"Error analyzing {image_path}: {e}")
        return 0.0

def analyze_and_delete(threshold=0.6, preview_only=True):
    """Analyze and optionally delete low quality faces."""
    conn = sqlite3.connect("faces.db")
    cursor = conn.cursor()
    
    try:
        # Get all faces
        cursor.execute("""
            SELECT id, filename, image_path, yearbook_year, school_name, page_number 
            FROM faces
        """)
        faces = cursor.fetchall()
        total_faces = len(faces)
        
        low_quality_faces = []
        processed = 0
        
        print(f"\nAnalyzing {total_faces} faces...")
        
        # Process in batches with progress bar
        for face in tqdm(faces, desc="Analyzing faces"):
            face_id, filename, image_path, year, school, page = face
            
            if not os.path.exists(image_path):
                continue
            
            quality_score = get_quality_score(image_path)
            
            if quality_score < threshold:
                low_quality_faces.append({
                    'id': face_id,
                    'filename': filename,
                    'path': image_path,
                    'score': quality_score,
                    'year': year,
                    'school': school,
                    'page': page
                })
        
        # Sort by quality score
        low_quality_faces.sort(key=lambda x: x['score'])
        
        # Print statistics
        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)
        print(f"Total faces analyzed: {total_faces}")
        print(f"Low quality faces found: {len(low_quality_faces)}")
        print(f"Percentage to be deleted: {(len(low_quality_faces)/total_faces)*100:.1f}%")
        
        # Show examples
        print("\nEXAMPLES OF LOWEST QUALITY FACES:")
        print("=" * 80)
        for face in low_quality_faces[:5]:
            print(f"\nQuality Score: {face['score']:.3f}")
            print(f"Filename: {face['filename']}")
            print(f"Year: {face['year']}")
            print(f"School: {face['school']}")
            print(f"Page: {face['page']}")
            print(f"Path: {face['path']}")
        
        if not preview_only:
            if input("\nProceed with deletion? (yes/no): ").lower() == 'yes':
                print("\nDeleting low quality faces...")
                deleted_count = 0
                
                for face in tqdm(low_quality_faces, desc="Deleting faces"):
                    try:
                        # Delete from database
                        cursor.execute("DELETE FROM faces WHERE id = ?", (face['id'],))
                        
                        # Delete file
                        if os.path.exists(face['path']):
                            os.remove(face['path'])
                            deleted_count += 1
                            
                    except Exception as e:
                        logging.error(f"Error deleting {face['filename']}: {e}")
                
                conn.commit()
                print(f"\nSuccessfully deleted {deleted_count} faces")
                
                # Show remaining count
                cursor.execute("SELECT COUNT(*) FROM faces")
                remaining = cursor.fetchone()[0]
                print(f"Remaining faces in database: {remaining}")
            else:
                print("\nDeletion cancelled")
        
    except Exception as e:
        logging.error(f"Database error: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    print("This script will identify and delete low quality face images.")
    print("Quality threshold set to 0.6")
    print("\nFirst, let's analyze your database...")
    
    # First run in preview mode
    analyze_and_delete(threshold=0.6, preview_only=True)
    
    if input("\nWould you like to proceed with deletion? (yes/no): ").lower() == 'yes':
        analyze_and_delete(threshold=0.6, preview_only=False)
    else:
        print("\nOperation cancelled") 
import logging
import os

from tqdm import tqdm

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='cleanup.log'
)

def cleanup_faces():
    """Remove incorrectly named face images"""
    print("Starting cleanup of incorrectly named face images...")
    
    faces_dir = "static/extracted_faces"
    if not os.path.exists(faces_dir):
        print(f"Directory {faces_dir} does not exist!")
        return
        
    # Get list of all face images
    face_files = [f for f in os.listdir(faces_dir) if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    print(f"Found {len(face_files)} total face images")
    deleted_count = 0
    kept_count = 0
    
    for face_file in tqdm(face_files, desc="Checking files"):
        # Check if filename matches the correct format: YEAR_SCHOOLNAME_pageX_faceY.jpg
        parts = face_file.replace('.jpg', '').replace('.jpeg', '').replace('.png', '').split('_')
        
        # File should be deleted if:
        # 1. Doesn't have enough parts
        # 2. First part isn't a 4-digit year
        # 3. Doesn't contain 'page' and 'face' in correct positions
        # 4. Has empty school name
        should_delete = False
        
        try:
            if len(parts) < 4:  # Need at least year, school, page, face
                should_delete = True
            elif not (parts[0].isdigit() and len(parts[0]) == 4):  # First part should be year
                should_delete = True
            elif not any(p.startswith('page') for p in parts):  # Should have 'page' somewhere
                should_delete = True
            elif not any(p.startswith('face') for p in parts):  # Should have 'face' somewhere
                should_delete = True
            elif len(''.join(parts[1:-2]).strip()) == 0:  # School name should not be empty
                should_delete = True
        except:
            should_delete = True
            
        if should_delete:
            try:
                file_path = os.path.join(faces_dir, face_file)
                os.remove(file_path)
                deleted_count += 1
                logging.info(f"Deleted incorrect file: {face_file}")
            except Exception as e:
                logging.error(f"Error deleting {face_file}: {e}")
        else:
            kept_count += 1
            
    print(f"\nCleanup complete!")
    print(f"Deleted: {deleted_count} incorrect files")
    print(f"Kept: {kept_count} correct files")
    
if __name__ == "__main__":
    cleanup_faces() 
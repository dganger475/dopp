import logging
import os
import pickle
import shutil

import face_recognition
import faiss
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

import numpy as np

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a minimal Flask app to provide configuration
app = Flask(__name__)
app.config.update(
    DB_PATH="faces.db",  # Main faces database in root
    INDEX_PATH="faces.index",
    MAP_PATH="faces_filenames.pkl"
)

def get_profile_pic_path():
    """Get path to the user's profile picture"""
    profile_dir = os.path.join("static", "profile_pics")
    
    # First look for the screenshot file
    screenshot_path = os.path.join(profile_dir, "Screenshot_2025-03-08_193903_1.png")
    if os.path.exists(screenshot_path):
        return screenshot_path
        
    # Otherwise look for any image in the profile_pics directory
    for filename in os.listdir(profile_dir):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
            return os.path.join(profile_dir, filename)
    
    # If nothing found, use default
    return os.path.join("static", "default_profile.png")

def extract_face_encoding(image_path):
    """Extract face encoding from the image"""
    try:
        logging.info(f"Loading image from: {image_path}")
        image = face_recognition.load_image_file(image_path)
        
        # Get all face locations
        face_locations = face_recognition.face_locations(image)
        logging.info(f"Found {len(face_locations)} faces in image")
        
        if not face_locations:
            logging.error(f"No faces detected in {image_path}")
            return None
            
        # Get encodings for all faces
        face_encodings = face_recognition.face_encodings(image, face_locations)
        
        if not face_encodings:
            logging.error(f"Failed to extract encodings from {image_path}")
            return None
            
        # Use the first face encoding
        return face_encodings[0]
        
    except Exception as e:
        logging.error(f"Error extracting face encoding: {e}")
        return None

def find_similar_faces(encoding, top_k=10):
    """Find similar faces using FAISS index"""
    if encoding is None:
        logging.error("Cannot search with None encoding")
        return []
        
    try:
        # Load the FAISS index and mapping
        index_path = app.config['INDEX_PATH']
        map_path = app.config['MAP_PATH']
        
        logging.info(f"Loading FAISS index from {index_path}")
        index = faiss.read_index(index_path)
        
        logging.info(f"Loading filename mapping from {map_path}")
        with open(map_path, "rb") as f:
            filenames = pickle.load(f)
            
        logging.info(f"Index contains {index.ntotal} vectors, mapping has {len(filenames)} filenames")
        
        # Ensure encoding is in correct format
        query = np.array([encoding], dtype=np.float32)
        
        # Search the index
        distances, indices = index.search(query, top_k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(filenames):
                continue
                
            filename = filenames[idx]
            similarity = max(0, min(99, int((1.0 - dist) * 100)))
            
            # Debug info
            logging.info(f"Match #{i+1}: {filename}, distance={dist:.4f}, similarity={similarity}%")
            
            results.append({
                "filename": filename,
                "image_path": f"/static/extracted_faces/{filename}",
                "similarity": similarity
            })
            
        return results
        
    except Exception as e:
        logging.error(f"Error searching FAISS index: {e}")
        return []

def create_results_image(profile_path, matches, output_path="match_results.jpg"):
    """Create visualization of matches"""
    # Size and layout
    image_size = 200
    padding = 10
    n_cols = 5
    n_rows = (len(matches) // n_cols) + 1
    
    # Create canvas
    width = image_size * n_cols + padding * (n_cols+1)
    height = image_size * (n_rows+1) + padding * (n_rows+2)
    result = Image.new("RGB", (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(result)
    
    # Add profile image at the top
    try:
        profile_img = Image.open(profile_path).convert("RGB")
        profile_img = profile_img.resize((image_size, image_size))
        result.paste(profile_img, (padding, padding))
        draw.text((padding*2 + image_size, padding + image_size//2), "YOUR PROFILE", fill=(0, 0, 0))
    except Exception as e:
        logging.error(f"Error adding profile image: {e}")
    
    # Add match images
    for i, match in enumerate(matches):
        row = (i // n_cols) + 1  # +1 for profile image row
        col = i % n_cols
        
        x = padding + col * (image_size + padding)
        y = padding + row * (image_size + padding)
        
        try:
            img_path = os.path.join("static", "extracted_faces", match["filename"])
            if os.path.exists(img_path):
                img = Image.open(img_path).convert("RGB")
                img = img.resize((image_size, image_size))
                result.paste(img, (x, y))
                
                # Add similarity text
                text = f"{match['similarity']}%"
                draw.text((x+5, y+5), text, fill=(255, 0, 0))
            else:
                draw.rectangle([x, y, x+image_size, y+image_size], outline=(0, 0, 0))
                draw.text((x+5, y+image_size//2), f"Image not found", fill=(255, 0, 0))
        except Exception as e:
            logging.error(f"Error adding match image {i}: {e}")
    
    # Save result
    result.save(output_path)
    logging.info(f"Saved result image to {output_path}")
    return output_path

def main():
    # Create output directory if it doesn't exist
    os.makedirs("output", exist_ok=True)
    
    # Get user profile picture
    profile_path = get_profile_pic_path()
    logging.info(f"Using profile picture: {profile_path}")
    
    # Extract face encoding from profile picture
    encoding = extract_face_encoding(profile_path)
    if encoding is None:
        logging.error("Failed to extract face encoding from profile picture!")
        return False
    
    # Find similar faces
    top_k = 20
    matches = find_similar_faces(encoding, top_k=top_k)
    logging.info(f"Found {len(matches)} similar faces")
    
    # Create visual result
    result_path = os.path.join("output", "match_results.jpg")
    create_results_image(profile_path, matches, result_path)
    
    # Copy to static folder for web viewing
    static_result = os.path.join("static", "match_results.jpg")
    shutil.copy(result_path, static_result)
    logging.info(f"Results available at: {static_result}")
    
    logging.info("\n" + "-"*50)
    logging.info("VIEW YOUR RESULTS AT: http://localhost:5000/static/match_results.jpg")
    logging.info("-"*50 + "\n")
    
    # Print match details
    for i, match in enumerate(matches):
        logging.info(f"Match #{i+1}: {match['filename']} (Similarity: {match['similarity']}%)")
    
    return True

if __name__ == "__main__":
    main()

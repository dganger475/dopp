import logging
import os

import face_recognition
from flask import Flask
from PIL import Image, ImageDraw, ImageFont

import numpy as np
from utils.face_recognition import extract_face_encoding

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Create a Flask app for context
app = Flask(__name__)
app.config.update({
    'DB_PATH': 'faces.db',
    'INDEX_PATH': 'faces.index',
    'MAP_PATH': 'faces_filenames.pkl'
})

def test_profile_image(image_path):
    """Test face encoding extraction from a profile image and visualize results"""
    
    # Create output directory if it doesn't exist
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)
    
    logging.info(f"Testing face encoding extraction for: {image_path}")
    
    # First use our improved function
    encoding = extract_face_encoding(image_path)
    
    if encoding is not None:
        logging.info("✅ Successfully extracted face encoding with improved function")
        logging.info(f"Encoding shape: {encoding.shape}")
        logging.info(f"Encoding sample: {encoding[:5]}")
    else:
        logging.error("❌ Failed to extract face encoding with improved function")
    
    # Now try to visualize the face detection
    try:
        # Load the image
        image = face_recognition.load_image_file(image_path)
        pil_image = Image.fromarray(image)
        
        # Try both detection models
        models = ["hog", "cnn"]
        for model in models:
            try:
                # Detect faces
                face_locations = face_recognition.face_locations(image, model=model)
                logging.info(f"Model {model}: Found {len(face_locations)} faces")
                
                # Create a copy for drawing
                draw_image = pil_image.copy()
                draw = ImageDraw.Draw(draw_image)
                
                # Draw boxes around faces
                for i, (top, right, bottom, left) in enumerate(face_locations):
                    # Draw rectangle
                    draw.rectangle(((left, top), (right, bottom)), outline="lime", width=3)
                    
                    # Add label
                    label = f"Face #{i+1}"
                    draw.text((left, top-20), label, fill="lime")
                    
                    # Try to get encoding for this face
                    try:
                        face_encoding = face_recognition.face_encodings(image, [face_locations[i]])[0]
                        encoding_status = "Encoding: Success"
                    except Exception as e:
                        encoding_status = f"Encoding: Failed ({str(e)})"
                    
                    draw.text((left, bottom+5), encoding_status, fill="lime")
                
                # Save the visualization
                output_filename = f"{os.path.basename(image_path)}_detected_{model}.jpg"
                output_path = os.path.join(output_dir, output_filename)
                draw_image.save(output_path)
                logging.info(f"Saved detection visualization to {output_path}")
            
            except Exception as e:
                logging.error(f"Error detecting faces with {model} model: {e}")
        
        # If faces were detected, test search with the encoding
        if encoding is not None:
            logging.info("Now testing similarity search with this encoding...")
            # Import directly from the module to avoid circular imports
            from utils.face_recognition import find_similar_faces_faiss
            
            try:
                # Search similar faces
                matches = find_similar_faces_faiss(encoding, top_k=10)
            except Exception as e:
                logging.error(f"Error during similarity search: {e}")
                matches = []
            
            if matches:
                logging.info(f"Found {len(matches)} similar faces")
                logging.info("Top 3 matches:")
                for i, match in enumerate(matches[:3], 1):
                    logging.info(f"  {i}. {match['filename']} - {match['similarity']}%")
                
                # Create a visualization of the matches
                vis_width = 600
                vis_height = 100 + (len(matches) * 110)
                vis_image = Image.new("RGB", (vis_width, vis_height), color="white")
                vis_draw = ImageDraw.Draw(vis_image)
                
                # Add the original image
                try:
                    original_img = pil_image.copy()
                    original_img.thumbnail((100, 100))
                    vis_image.paste(original_img, (10, 10))
                    vis_draw.text((120, 40), "Your Profile Image", fill="black")
                except Exception as e:
                    logging.error(f"Error adding profile image to visualization: {e}")
                
                # Add the matches
                try:
                    for i, match in enumerate(matches):
                        y_pos = 120 + (i * 110)
                        # Draw match info
                        vis_draw.text((120, y_pos), f"Match #{i+1}: {match['similarity']}%", fill="black")
                        vis_draw.text((120, y_pos+20), f"File: {match['filename']}", fill="black")
                        
                        # Try to load and add the match image
                        try:
                            match_path = os.path.join("static", "extracted_faces", match['filename'])
                            if os.path.exists(match_path):
                                match_img = Image.open(match_path)
                                match_img.thumbnail((100, 100))
                                vis_image.paste(match_img, (10, y_pos))
                            else:
                                vis_draw.rectangle(((10, y_pos), (110, y_pos+100)), outline="red")
                                vis_draw.text((15, y_pos+40), "Image not found", fill="red")
                        except Exception as e:
                            logging.error(f"Error adding match image {i}: {e}")
                            
                    # Save the visualization
                    matches_vis_path = os.path.join(output_dir, f"{os.path.basename(image_path)}_matches.jpg")
                    vis_image.save(matches_vis_path)
                    logging.info(f"Saved matches visualization to {matches_vis_path}")
                except Exception as e:
                    logging.error(f"Error creating matches visualization: {e}")
            else:
                logging.warning("No matches found!")
        
    except Exception as e:
        logging.error(f"Error creating visualization: {e}")

def main():
    """Test profile images for face encoding extraction"""
    logging.info("Starting profile encoding test")
    
    # Test with profile images in the profile_pics directory
    profile_pics_dir = os.path.join("static", "profile_pics")
    if not os.path.exists(profile_pics_dir):
        logging.error(f"Profile pics directory not found: {profile_pics_dir}")
        return False
    
    # Find all profile images
    profile_images = [
        os.path.join(profile_pics_dir, filename) 
        for filename in os.listdir(profile_pics_dir)
        if filename.lower().endswith(('.jpg', '.jpeg', '.png'))
    ]
    
    logging.info(f"Found {len(profile_images)} profile images")
    
    # Test each image within application context
    with app.app_context():
        for image_path in profile_images:
            test_profile_image(image_path)
    
    logging.info("Profile encoding tests complete")
    return True

if __name__ == "__main__":
    main()

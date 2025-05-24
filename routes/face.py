"""
Face Routes Module
================

This module contains routes related to face operations, including:
- Face image serving
- Face comparison
- Face metadata
"""
from flask import Blueprint, current_app, jsonify, render_template, request, send_file, session, url_for
from flask_login import current_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import sqlite3
from models.user import User
from utils.db.database import get_db_connection
# from utils.face.recognition import FaceRecognizer  # Comment out or remove this line
from utils.files.image_handler import ImageHandler
from utils.index.faiss_manager import FaissIndexManager 
from utils.csrf import csrf
from .config import get_image_paths, get_db_path, get_default_profile_image_path

face = Blueprint('face', __name__)

# Initialize the limiter
limiter = Limiter(key_func=get_remote_address)

@face.route('/load_image', methods=['POST'])
@csrf.exempt
@login_required
@limiter.exempt  # Exempt this route from rate limiting to allow multiple image loads
def load_image():
    # Your existing code here
    pass

@face.route('/image/<int:face_id>')
@limiter.exempt  # Exempt this route from rate limiting to allow multiple image loads
def serve_face_image_by_id(face_id):
    """Serve face images directly by ID from the extracted_faces directory"""
    try:
        import traceback
        import glob
        
        current_app.logger.warning(f"[DIAGNOSTIC] Processing face ID: {face_id} in public route")

        # Use direct SQLite connection instead of SQLAlchemy
        conn = None
        try:
            conn = get_db_connection()
            if not conn:
                current_app.logger.error("Failed to get database connection")
                return send_default_image()
                
            cursor = conn.cursor()
            cursor.execute("SELECT filename FROM faces WHERE id = ?", (face_id,))
            result = cursor.fetchone()
            
            # Close the connection as soon as we're done with it
            conn.close()
            conn = None # Set to None to ensure it's not closed again in finally block
            
            if result and result[0]:
                filename = result[0]
                current_app.logger.warning(f"[DIAGNOSTIC] Found filename in DB: {filename}")
                
                # First try direct match in extracted_faces (absolute path)
                direct_path = os.path.join(current_app.root_path, 'static', 'extracted_faces', filename)
                current_app.logger.warning(f"[DIAGNOSTIC] Trying direct path: {direct_path}")
                if os.path.exists(direct_path):
                    current_app.logger.warning(f"[DIAGNOSTIC] Found direct match: {direct_path}")
                    return send_file(direct_path, mimetype='image/jpeg')
                
                # Try a case-insensitive match for yearbook files in extracted_faces
                extracted_faces_dir = os.path.join(current_app.root_path, 'static', 'extracted_faces')
                if os.path.exists(extracted_faces_dir):
                    for file in os.listdir(extracted_faces_dir):
                        if file.lower() == filename.lower() or (
                            'yearbook' in filename.lower() and 'yearbook' in file.lower() and 
                            file.lower().endswith(filename.lower()[-10:])):
                            match_path = os.path.join(extracted_faces_dir, file)
                            current_app.logger.warning(f"[DIAGNOSTIC] Found case-insensitive match: {match_path}")
                            return send_file(match_path, mimetype='image/jpeg')
                
                # Try partial match for yearbook files
                if 'yearbook' in filename.lower() or 'foxcollege' in filename.lower():
                    # Extract key parts from filename for pattern matching
                    parts = filename.split('_')
                    if len(parts) >= 2:
                        # Try to match the last part which often has page/face numbers
                        pattern_suffix = parts[-1]
                        pattern = os.path.join(extracted_faces_dir, f"*{pattern_suffix}")
                        matches = glob.glob(pattern)
                        if matches:
                            current_app.logger.warning(f"[DIAGNOSTIC] Found suffix pattern match: {matches[0]}")
                            return send_file(matches[0], mimetype='image/jpeg')
                
                # Try all possible image paths from config
                possible_paths = get_image_paths(filename)
                for image_path in possible_paths:
                    if os.path.exists(image_path):
                        current_app.logger.warning(f"[DIAGNOSTIC] Serving image from config path: {image_path}")
                        return send_file(image_path, mimetype='image/jpeg')
                
                # Try to find any image with the face ID at the end of filename in extracted_faces
                pattern = os.path.join(extracted_faces_dir, f"*f{face_id % 100}.jpg")
                matches = glob.glob(pattern)
                if matches:
                    current_app.logger.warning(f"[DIAGNOSTIC] Found face number match: {matches[0]}")
                    return send_file(matches[0], mimetype='image/jpeg')
                
                # Last resort: use a modulo-based approach to consistently serve any available image
                all_images = glob.glob(os.path.join(extracted_faces_dir, "*.jpg"))
                if all_images:
                    index = face_id % len(all_images)
                    current_app.logger.warning(f"[DIAGNOSTIC] Using fallback image {index+1} of {len(all_images)}: {all_images[index]}")
                    return send_file(all_images[index], mimetype='image/jpeg')
                
                # If still nothing found, check the faces folder as final fallback
                faces_dir = os.path.join(current_app.root_path, 'static', 'faces')
                all_face_images = glob.glob(os.path.join(faces_dir, "*.jpg"))
                if all_face_images:
                    index = face_id % len(all_face_images)
                    current_app.logger.warning(f"[DIAGNOSTIC] Using faces folder fallback: {all_face_images[index]}")
                    return send_file(all_face_images[index], mimetype='image/jpeg')
                
                current_app.logger.error(f"[DIAGNOSTIC] Image not found in any location: {filename}")
                return send_default_image()
            else:
                current_app.logger.warning(f"[DIAGNOSTIC] No face found with ID {face_id}")
                return send_default_image()
                
        except Exception as query_error:
            current_app.logger.error(f"[DIAGNOSTIC] Query error in serve_face_image_by_id: {query_error}")
            current_app.logger.error(traceback.format_exc())
            return send_default_image()
            
    except Exception as e:
        import traceback
        current_app.logger.error(f"[DIAGNOSTIC] Error in serve_face_image_by_id: {e}")
        current_app.logger.error(traceback.format_exc())
        return send_default_image()
    finally:
        # Ensure connection is closed if it was opened and not already closed
        if conn is not None:
            conn.close()

@face.route('/view/<int:face_id>')
def direct_face_view(face_id):
    """Ultra-simple face viewer with direct HTML"""
    conn = None
    try:
        # Connect to the faces database
        conn = sqlite3.connect(get_db_path())
        conn.row_factory = sqlite3.Row  # This enables column access by name
        cursor = conn.cursor()
        
        # Query the faces table by ID
        cursor.execute("SELECT * FROM faces WHERE id = ?", (face_id,))
        face = cursor.fetchone()
        
        if not face:
            current_app.logger.warning(f"Face with ID {face_id} not found in database")
            return render_template('error.html', message="Face not found"), 404
            
        # Get user info if logged in
        user_id = session.get('user_id')
        user = None # Initialize user to None
        if user_id:
            try:
                user = User.get_by_id(user_id)
            except Exception as e:
                current_app.logger.error(f"Error getting user by ID in direct_face_view: {e}")

        username = "Guest"
        profile_image_url = url_for('static', filename='default_profile.png')

        if user:
            username = user.username
            # Clean up profile_image path if needed
            profile_image = user.profile_image
            if profile_image and profile_image.startswith('/'):
                profile_image = profile_image[1:]  # Remove leading slash
            # Generate proper URLs
            profile_image_url = url_for('static', filename=f'profile_pics/{profile_image}') if profile_image else url_for('static', filename='default_profile.png')

        # Calculate similarity
        similarity = 85  # Default similarity
        if face and 'distance' in face.keys() and face['distance'] is not None:
            threshold = 0.6
            distance = float(face['distance'])
            similarity = max(0, 100 * (1 - (distance / threshold)))
            similarity = round(similarity, 1)  # Round to 1 decimal place
        
        # Extract face metadata
        filename = face['filename']
        decade = face['decade'] or "Unknown"
        state = face['state'] or "Unknown"
        
        # Get face image URL
        face_image_url = None
        possible_paths = get_image_paths(filename)
        
        # Check which path exists and use the first one found
        for path in possible_paths:
            if os.path.exists(path):
                # If the path is already relative to static, use it as is
                if 'static' in path:
                    face_image_url = '/' + os.path.relpath(path, current_app.root_path)
                else:
                    face_image_url = url_for('static', filename=os.path.relpath(path, os.path.join(current_app.root_path, 'static')))
                break
                
        # Fallback to the original path if nothing found (will show broken image)
        if not face_image_url:
            face_image_url = url_for('static', filename=f'extracted_faces/{filename}')
        
        # Generate a simple HTML response with improved styling
        html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Face View | {face_id}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
        <style>
            body {{ 
                background: #121212; 
                color: white; 
                font-family: 'Roboto', sans-serif; 
                text-align: center; 
                margin: 0; 
                padding: 0; 
            }}
            .header {{ 
                background: #333; 
                padding: 1rem;
                margin-bottom: 2rem;
            }}
            .container {{
                max-width: 800px;
                margin: 0 auto;
                padding: 1rem;
            }}
            .face-image {{
                max-width: 100%;
                height: auto;
                border-radius: 8px;
                margin-bottom: 1rem;
            }}
            .metadata {{
                background: #1e1e1e;
                padding: 1rem;
                border-radius: 8px;
                margin-bottom: 1rem;
            }}
            .similarity {{
                font-size: 1.2rem;
                font-weight: bold;
                color: #4CAF50;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Face #{face_id}</h1>
        </div>
        <div class="container">
            <img src="{face_image_url}" alt="Face #{face_id}" class="face-image">
            <div class="metadata">
                <p>Decade: {decade}</p>
                <p>State: {state}</p>
                <p class="similarity">Similarity: {similarity}%</p>
            </div>
        </div>
    </body>
    </html>
    '''
        return html

    except Exception as e:
        current_app.logger.error(f"Error in direct_face_view: {e}")
        return render_template('error.html', message="An error occurred"), 500
    finally:
        if conn:
            conn.close()

def send_default_image():
    """Helper function to send the default profile image."""
    return send_file(get_default_profile_image_path(), mimetype='image/png')
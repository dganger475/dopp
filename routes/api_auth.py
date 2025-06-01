"""
API Authentication Routes for React Frontend

This module provides authentication endpoints for the React frontend,
including registration with face image upload and processing.
"""

import os
import logging
import uuid
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from models.user import User
from utils.face.indexing import index_profile_face
from middleware.security import sanitize_input
from routes.auth import validate_password_strength
from routes.config import get_default_profile_image_path


def save_profile_photo(file_obj, user_id):
    """
    Save a profile photo to the appropriate directory and return the filename.
    
    Args:
        file_obj: The uploaded file object from request.files
        user_id: The ID of the user who uploaded the photo
        
    Returns:
        str: The filename of the saved photo or None if saving failed
    """
    try:
        if not file_obj:
            return None
            
        # Get the original filename and create a secure version
        original_filename = file_obj.filename
        extension = os.path.splitext(original_filename)[1].lower()
        
        # Only allow certain file extensions
        if extension not in ['.jpg', '.jpeg', '.png', '.gif']:
            current_app.logger.warning(f"Invalid file extension: {extension}")
            return None
            
        # Create a unique filename using user_id and a random string
        unique_id = uuid.uuid4().hex[:8]
        filename = f"profile_{user_id}_{unique_id}{extension}"
        
        # Define the path to save the file
        profile_pics_dir = os.path.join(current_app.root_path, 'static', 'profile_pics')
        os.makedirs(profile_pics_dir, exist_ok=True)
        
        # Save the file
        file_path = os.path.join(profile_pics_dir, filename)
        file_obj.save(file_path)
        
        current_app.logger.info(f"Saved profile photo for user {user_id}: {filename}")
        return filename
        
    except Exception as e:
        current_app.logger.error(f"Error saving profile photo: {str(e)}")
        return None

# Set up logging
logger = logging.getLogger(__name__)

# Create blueprint
api_auth = Blueprint('api_auth', __name__, url_prefix='/auth')

@api_auth.route('/register', methods=['POST'])
def register():
    """Handle user registration with face image upload for React frontend"""
    try:
        # Check if form data is present
        if 'username' not in request.form or 'email' not in request.form or 'password' not in request.form:
            return jsonify({
                'status': 'error',
                'message': 'Username, email, and password are required'
            }), 400
            
        # Get form data
        username = sanitize_input(request.form.get('username', '').strip())
        email = sanitize_input(request.form.get('email', '').strip().lower())
        password = request.form.get('password', '')
        
        # Validate inputs
        if not username or not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Username, email, and password cannot be empty'
            }), 400
            
        # Check if face image was uploaded
        if 'face_image' not in request.files:
            return jsonify({
                'status': 'error',
                'message': 'Face image is required'
            }), 400
            
        face_image = request.files['face_image']
        if face_image.filename == '':
            return jsonify({
                'status': 'error',
                'message': 'No face image selected'
            }), 400
            
        # Validate password strength
        try:
            validate_password_strength(password)
        except Exception as e:
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 400
            
        # Check for existing user
        if User.get_by_username(username):
            return jsonify({
                'status': 'error',
                'message': 'Username already exists'
            }), 400
            
        if User.get_by_email(email):
            return jsonify({
                'status': 'error',
                'message': 'Email already registered'
            }), 400
            
        # Create user
        user = User.create(
            username=username,
            email=email,
            password=password
        )
        
        if not user:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create user'
            }), 500
            
        # Handle profile photo
        try:
            filename = save_profile_photo(face_image, user.id)
            if filename:
                user.update(profile_image=filename)
                # Extract face encodings and add to FAISS index
                indexed_face = index_profile_face(filename, user.id, username)
                if not indexed_face:
                    logger.warning(f"Face indexing failed for user {username} (ID: {user.id})")
        except Exception as e:
            logger.error(f"Profile photo processing failed: {str(e)}")
            # Set default profile image if face processing fails
            default_image = os.path.basename(get_default_profile_image_path())
            user.update(profile_image=default_image)
            
        # Return success response
        return jsonify({
            'status': 'success',
            'message': 'Registration successful',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })
        
    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return jsonify({
            'status': 'error',
            'message': 'An error occurred during registration'
        }), 500

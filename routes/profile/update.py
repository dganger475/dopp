import os
import uuid
from flask import request, jsonify, current_app, session, Blueprint
from werkzeug.utils import secure_filename
from utils.csrf import csrf
from models.user import User
from routes.auth import login_required

# Create a blueprint for profile update
profile_update = Blueprint('profile_update', __name__)

# Define allowed file extensions for profile images
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@profile_update.route('/update/<int:user_id>', methods=['POST'])
@csrf.exempt
@login_required
def update_profile(user_id):
    """Update user profile information.
    
    This endpoint handles updating user profile information including:
    - Basic info (name, username, bio, etc.)
    - Profile image
    - Cover photo
    """
    try:
        current_user_id = session.get('user_id')
        origin = request.headers.get('Origin')
        if not current_user_id or int(current_user_id) != user_id:
            response = jsonify({
                'status': 'error',
                'message': 'Unauthorized to update this profile'
            })
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response, 403
        
        # Get the user from the database
        user = User.get_by_id(user_id)
        if not user:
            response = jsonify({
                'status': 'error',
                'message': 'User not found'
            })
            if origin:
                response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response, 404
        
        # Collect updates
        updates = {}
        
        # Process text fields
        if 'full_name' in request.form:
            updates['full_name'] = request.form.get('full_name')
        
        if 'username' in request.form:
            new_username = request.form.get('username')
            # Check if username is already taken by another user
            if new_username != user.username:
                existing_user = User.get_by_username(new_username)
                if existing_user and existing_user.id != user_id:
                    response = jsonify({
                        'status': 'error',
                        'message': 'Username already taken'
                    })
                    if origin:
                        response.headers['Access-Control-Allow-Origin'] = origin
                    response.headers['Access-Control-Allow-Credentials'] = 'true'
                    return response, 400
            updates['username'] = new_username
        
        if 'bio' in request.form:
            updates['bio'] = request.form.get('bio')
        
        # Handle both field names for backward compatibility
        if 'current_location_city' in request.form:
            updates['current_location_city'] = request.form.get('current_location_city')
        elif 'current_city' in request.form:
            updates['current_location_city'] = request.form.get('current_city')
        
        if 'hometown' in request.form:
            updates['hometown'] = request.form.get('hometown')
        
        if 'email' in request.form:
            updates['email'] = request.form.get('email')
        
        if 'phone' in request.form:
            updates['phone'] = request.form.get('phone')
        
        # Process profile image
        if 'profile_image' in request.files:
            profile_image = request.files['profile_image']
            if profile_image and allowed_file(profile_image.filename):
                # Create a unique filename
                filename = secure_filename(profile_image.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                
                # Save the file in both profile_pics and images directories for redundancy
                upload_folders = [
                    os.path.join(current_app.static_folder, 'profile_pics'),
                    os.path.join(current_app.static_folder, 'images')
                ]
                
                for upload_folder in upload_folders:
                    os.makedirs(upload_folder, exist_ok=True)
                    file_path = os.path.join(upload_folder, unique_filename)
                    profile_image.save(file_path)
                    current_app.logger.info(f"Saved profile image to: {file_path}")
                
                # Update the user's profile image
                updates['profile_image'] = unique_filename
        
        # Process cover photo
        if 'cover_photo' in request.files:
            cover_photo = request.files['cover_photo']
            if cover_photo and allowed_file(cover_photo.filename):
                # Create a unique filename
                filename = secure_filename(cover_photo.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                
                # Save the file
                upload_folder = os.path.join(current_app.static_folder, 'cover_photos')
                os.makedirs(upload_folder, exist_ok=True)
                file_path = os.path.join(upload_folder, unique_filename)
                cover_photo.save(file_path)
                
                # Update the user's cover photo with the relative path
                cover_photo_path = f"/static/cover_photos/{unique_filename}"
                updates['cover_photo'] = cover_photo_path
                current_app.logger.info(f"Saved cover photo to: {cover_photo_path}")
                current_app.logger.info(f"Cover photo path in updates: {updates['cover_photo']}")
        
        # Update the user in the database
        if updates:
            user.update(**updates)
            
            # Return the updated user data
            response = jsonify({
                'status': 'success',
                'message': 'Profile updated successfully',
                'user': user.to_dict()
            })
        else:
            response = jsonify({
                'status': 'warning',
                'message': 'No changes were made',
                'user': user.to_dict()
            })
        
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
    
    except Exception as e:
        current_app.logger.error(f"Error updating profile: {str(e)}")
        response = jsonify({
            'status': 'error',
            'message': f"Failed to update profile: {str(e)}"
        })
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response, 500

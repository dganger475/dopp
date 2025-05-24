"""
Profile Helpers Module
=================

This module contains helper functions for profile-related operations.
"""
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify, flash, current_app
import os, traceback, secrets, time
from werkzeug.utils import secure_filename
from routes.auth import login_required
from models.user import User
from utils.image_paths import get_image_path, normalize_profile_image_path
from forms.profile_forms import ProfileEditForm
from ..config import get_profile_image_path

helpers = Blueprint('helpers', __name__)

def allowed_file(filename):
    """Check if the file extension is allowed."""
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image(file, folder, is_profile=False, user_id=None):
    """Save an uploaded image file to the specified folder."""
    current_app.logger.info(f"[save_image] CALLED with file={getattr(file, 'filename', None)}, folder={folder}, is_profile={is_profile}, user_id={user_id}")
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        base_name, extension = os.path.splitext(filename)
        # Remove _pending suffix if it exists
        base_name = base_name.replace('_pending', '')
        new_filename = f"{base_name}_{user_id}_{os.urandom(4).hex()}{extension}"
        
        # Get the absolute path from configuration if it's a profile image
        if is_profile and folder == 'static/profile_pics':
            if current_app.config.get('PROFILE_PICS'):
                absolute_folder_path = current_app.config['PROFILE_PICS']
            else:
                absolute_folder_path = os.path.join(current_app.root_path, folder)
        else:
            absolute_folder_path = os.path.join(current_app.root_path, folder)
        
        os.makedirs(absolute_folder_path, exist_ok=True)
        save_path = os.path.join(absolute_folder_path, new_filename)
        
        try:
            file.save(save_path)
            current_app.logger.info(f"[save_image] File saved to: {save_path}")
            return new_filename
        except Exception as e:
            current_app.logger.error(f"[save_image] Error saving file: {e}", exc_info=True)
            return None
    
    current_app.logger.warning(f"[save_image] File not saved: {getattr(file, 'filename', 'No filename')}")
    return None

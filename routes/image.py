"""
Image Routes Module
=================

This module contains routes related to image operations, including:
- Image serving
- Image processing
- Image utilities
"""
from flask import Blueprint, current_app, jsonify, render_template, request, send_file
from flask_login import current_user, login_required
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
import sqlite3
from utils.db.database import get_db_connection
from .config import get_image_paths, get_default_profile_image_path

image = Blueprint('image', __name__)

@image.route('/direct-match-image/<int:match_id>')
@limiter.exempt  # Exempt this route from rate limiting to allow multiple image loads
def get_direct_match_image(match_id):
    """Serve match images directly from the extracted_faces directory"""
    try:
        import traceback
        
        current_app.logger.warning(f"[DIAGNOSTIC] Processing match_id: {match_id} in public route")

        # Use direct SQLite connection instead of SQLAlchemy
        try:
            conn = get_db_connection()
            if not conn:
                current_app.logger.error("Failed to get database connection")
                return send_default_image()
                
            cursor = conn.cursor()
            cursor.execute("SELECT filename FROM faces WHERE id = ?", (match_id,))
            result = cursor.fetchone()
            
            # Close the connection as soon as we're done with it
            conn.close()
            
            if result and result[0]:
                filename = result[0]
                current_app.logger.warning(f"[DIAGNOSTIC] Found filename: {filename}")
                
                # Try all possible image paths
                possible_paths = get_image_paths(filename)
                for image_path in possible_paths:
                    if os.path.exists(image_path):
                        current_app.logger.warning(f"[DIAGNOSTIC] Serving image from: {image_path}")
                        return send_file(image_path, mimetype='image/jpeg')
                
                current_app.logger.error(f"[DIAGNOSTIC] Image not found in any location: {filename}")
                return send_default_image()
            else:
                current_app.logger.warning(f"[DIAGNOSTIC] No face found with ID {match_id}")
                return send_default_image()
                
        except Exception as query_error:
            current_app.logger.error(f"[DIAGNOSTIC] Query error: {query_error}")
            current_app.logger.error(traceback.format_exc())
            return send_default_image()
            
    except Exception as e:
        import traceback
        current_app.logger.error(f"[DIAGNOSTIC] Error in get_direct_match_image: {e}")
        current_app.logger.error(traceback.format_exc())
        return send_default_image()

def send_default_image():
    """Helper function to send the default profile image."""
    return send_file(get_default_profile_image_path(), mimetype='image/png') 
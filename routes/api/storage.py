"""
Storage API endpoints for handling B2 image URLs with optimization.
"""

from flask import Blueprint, send_file, current_app, request
from utils.db.storage import get_storage
from utils.files.utils import is_anonymized_face_filename
from PIL import Image
import io
import logging

storage_api = Blueprint('storage_api', __name__)
logger = logging.getLogger(__name__)

def optimize_image(image_data, format='jpeg', quality=80, width=None, height=None):
    """Optimize an image with the given parameters."""
    try:
        # Open image from bytes
        img = Image.open(io.BytesIO(image_data))
        
        # Resize if dimensions provided
        if width or height:
            # Calculate new dimensions maintaining aspect ratio
            if width and height:
                new_size = (width, height)
            elif width:
                ratio = width / img.width
                new_size = (width, int(img.height * ratio))
            else:
                ratio = height / img.height
                new_size = (int(img.width * ratio), height)
            
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed (for JPEG)
        if format.lower() == 'jpeg' and img.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        # Save optimized image to bytes
        output = io.BytesIO()
        img.save(output, format=format, quality=quality, optimize=True)
        output.seek(0)
        
        return output
    except Exception as e:
        logger.error(f"Error optimizing image: {str(e)}")
        return None

@storage_api.route('/faces/<filename>')
def get_face_image(filename):
    """Get a face image from B2 storage with optimization."""
    try:
        # Verify it's an anonymized filename
        if not is_anonymized_face_filename(filename):
            logger.warning(f"Invalid face filename format: {filename}")
            return current_app.config.get('DEFAULT_FACE_IMAGE', '/static/default_face.jpg')
        
        # Get optimization parameters
        format = request.args.get('format', 'jpeg').lower()
        quality = int(request.args.get('quality', 80))
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        
        # Get file from storage backend
        storage = get_storage()
        file_data = storage.get_file(filename, folder='faces')
        
        if not file_data:
            return current_app.config.get('DEFAULT_FACE_IMAGE', '/static/default_face.jpg')
        
        # Optimize image
        optimized_data = optimize_image(
            file_data,
            format=format,
            quality=quality,
            width=width,
            height=height
        )
        
        if not optimized_data:
            return current_app.config.get('DEFAULT_FACE_IMAGE', '/static/default_face.jpg')
        
        return send_file(
            optimized_data,
            mimetype=f'image/{format}',
            cache_timeout=3600  # Cache for 1 hour
        )
        
    except Exception as e:
        logger.error(f"Error getting face image: {str(e)}")
        return current_app.config.get('DEFAULT_FACE_IMAGE', '/static/default_face.jpg')

@storage_api.route('/profile_pics/<filename>')
def get_profile_image(filename):
    """Get a profile image from B2 storage with optimization."""
    try:
        # Get optimization parameters
        format = request.args.get('format', 'jpeg').lower()
        quality = int(request.args.get('quality', 80))
        width = request.args.get('width', type=int)
        height = request.args.get('height', type=int)
        
        # Get file from storage backend
        storage = get_storage()
        file_data = storage.get_file(filename, folder='profile_pics')
        
        if not file_data:
            return current_app.config.get('DEFAULT_PROFILE_IMAGE', '/static/default_profile.jpg')
        
        # Optimize image
        optimized_data = optimize_image(
            file_data,
            format=format,
            quality=quality,
            width=width,
            height=height
        )
        
        if not optimized_data:
            return current_app.config.get('DEFAULT_PROFILE_IMAGE', '/static/default_profile.jpg')
        
        return send_file(
            optimized_data,
            mimetype=f'image/{format}',
            cache_timeout=3600  # Cache for 1 hour
        )
        
    except Exception as e:
        logger.error(f"Error getting profile image: {str(e)}")
        return current_app.config.get('DEFAULT_PROFILE_IMAGE', '/static/default_profile.jpg') 
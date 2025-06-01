"""
File validation utilities.
This module provides functions for validating file uploads.
"""

import imghdr
import logging
import os

import magic
from flask import current_app
from werkzeug.utils import secure_filename

# Configure logging
logger = logging.getLogger(__name__)

# Allowed file extensions and MIME types
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/gif", "image/webp"}


def allowed_file(filename, allowed_extensions=None):
    """Check if a file has an allowed extension."""
    if allowed_extensions is None:
        allowed_extensions = ALLOWED_IMAGE_EXTENSIONS

    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def validate_image_file(file):
    """
    Validate an uploaded image file.

    Args:
        file: The uploaded file object

    Returns:
        tuple: (is_valid, error_message)
    """
    if not file:
        return False, "No file provided"

    # Check if the filename is secure
    filename = secure_filename(file.filename)
    if not filename:
        return False, "Invalid filename"

    # Check file extension
    if not allowed_file(filename):
        return (
            False,
            f"File extension not allowed. Allowed extensions: {', '.join(ALLOWED_IMAGE_EXTENSIONS)}",
        )

    # Check file size
    max_size = current_app.config.get(
        "MAX_CONTENT_LENGTH", 16 * 1024 * 1024
    )  # Default 16MB
    if file.content_length and file.content_length > max_size:
        return False, f"File too large. Maximum size: {max_size / (1024 * 1024):.1f}MB"

    # Check MIME type using python-magic
    try:
        # Read the first 2048 bytes for MIME detection
        file_head = file.stream.read(2048)
        file.stream.seek(0)  # Reset file pointer

        mime = magic.from_buffer(file_head, mime=True)
        if mime not in ALLOWED_IMAGE_MIMES:
            return False, f"File type not allowed. Detected: {mime}"

        # Additional validation for images
        file.stream.seek(0)  # Reset file pointer
        file_head = file.stream.read(2048)
        file.stream.seek(0)  # Reset file pointer

        # Use imghdr to validate image format
        image_format = imghdr.what(None, file_head)
        if not image_format:
            return False, "Invalid image format"

        return True, None
    except Exception as e:
        logger.error(f"Error validating file: {e}")
        return False, "Error validating file"


def save_validated_file(file, upload_folder=None, filename=None):
    """
    Save a validated file to the upload folder.

    Args:
        file: The validated file object
        upload_folder: The folder to save the file to (default: app.config['UPLOAD_FOLDER'])
        filename: The filename to use (default: secure_filename(file.filename))

    Returns:
        tuple: (success, filepath or error_message)
    """
    if not file:
        return False, "No file provided"

    # Get upload folder
    if upload_folder is None:
        upload_folder = current_app.config["UPLOAD_FOLDER"]

    # Ensure upload folder exists
    os.makedirs(upload_folder, exist_ok=True)

    # Get filename
    if filename is None:
        filename = secure_filename(file.filename)

    # Save file
    try:
        filepath = os.path.join(upload_folder, filename)
        file.save(filepath)
        return True, filepath
    except Exception as e:
        logger.error(f"Error saving file: {e}")
        return False, f"Error saving file: {e}"

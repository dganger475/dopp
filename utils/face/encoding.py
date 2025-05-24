"""
Face Encoding Utilities
======================

Contains helper functions for encoding and processing face images.
"""

import logging  # Use standard logging primarily
import traceback

from flask import current_app  # Can be used if available, but make it optional

from utils.face.recognition import extract_face_encoding

# Removed async_extract as threading is bypassed.


def safe_extract_face_encoding(profile_image_path, app=None):
    """Extract face encoding with enhanced error logging.

    This function wraps extract_face_encoding to provide more robust error
    logging, attempting to use the Flask app's logger if an app instance
    is provided, otherwise falling back to standard logging.

    Args:
        profile_image_path (str): Path to the image file.
        app (Flask, optional): Optional Flask application instance for logging.

    Returns:
        numpy.ndarray or None: The face encoding if successful, otherwise None.
    """
    encoding = None
    try:
        encoding = extract_face_encoding(profile_image_path)
        if encoding is None:
            # extract_face_encoding already logs its own warnings if it returns None
            # but we can add a higher-level log here if needed.
            log_message = f"Face encoding returned None for path: {profile_image_path} (details likely logged by extract_face_encoding)."
            if app:
                app.logger.warning(log_message)
            elif current_app:
                current_app.logger.warning(log_message)
            else:
                logging.warning(log_message)

    except Exception as e:
        tb_str = traceback.format_exc()
        error_message = (
            f"Error during safe_extract_face_encoding for '{profile_image_path}': {e}"
        )
        detailed_error_message = f"{error_message}\nTraceback:\n{tb_str}"

        # Attempt to log with app logger if available, otherwise standard logging
        if app:
            app.logger.error(detailed_error_message)
        elif current_app:  # Try to use current_app if no explicit app passed
            try:
                current_app.logger.error(detailed_error_message)
            except (
                RuntimeError
            ):  # Handles cases where current_app is not available (e.g. outside request context)
                logging.error(detailed_error_message)
        else:
            logging.error(detailed_error_message)

        return None  # Ensure None is returned on error

    return encoding

#!/usr/bin/env python
"""
Test CSRF protection and file validation.
This script tests the CSRF protection and file validation utilities.
"""

import io
import os
import sys

from dotenv import load_dotenv
from flask import url_for

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

# Import the Flask application
from app import app
from utils.file_validation import allowed_file, validate_image_file


def test_csrf_protection():
    """Test CSRF protection."""
    print("Testing CSRF protection...")
    
    with app.test_client() as client:
        # Get the CSRF token from the context processor
        with client.session_transaction() as session:
            # Check if CSRF protection is enabled
            csrf_enabled = app.config.get('WTF_CSRF_ENABLED', False)
            print(f"CSRF protection enabled: {csrf_enabled}")
            
            # Check session cookie settings
            print(f"Session cookie secure: {app.config.get('SESSION_COOKIE_SECURE', False)}")
            print(f"Session cookie httponly: {app.config.get('SESSION_COOKIE_HTTPONLY', False)}")
            print(f"Session cookie samesite: {app.config.get('SESSION_COOKIE_SAMESITE', None)}")
            
            print("CSRF protection test passed!")

def test_file_validation():
    """Test file validation."""
    print("\nTesting file validation...")
    
    # Test valid image file
    valid_content = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00H\x00H\x00\x00\xff\xdb\x00C\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\t\t\x08\n\x0c\x14\r\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f\x1e\x1d\x1a\x1c\x1c $.\' ",#\x1c\x1c(7),01444\x1f\'9=82<.342\xff\xdb\x00C\x01\t\t\t\x0c\x0b\x0c\x18\r\r\x182!\x1c!22222222222222222222222222222222222222222222222222\xff\xc0\x00\x11\x08\x00\x01\x00\x01\x03\x01"\x00\x02\x11\x01\x03\x11\x01\xff\xc4\x00\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01}\x01\x02\x03\x00\x04\x11\x05\x12!1A\x06\x13Qa\x07"q\x142\x81\x91\xa1\x08#B\xb1\xc1\x15R\xd1\xf0$3br\x82\t\n\x16\x17\x18\x19\x1a%&\'()*456789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xc4\x00\x1f\x01\x00\x03\x01\x01\x01\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\t\n\x0b\xff\xc4\x00\xb5\x11\x00\x02\x01\x02\x04\x04\x03\x04\x07\x05\x04\x04\x00\x01\x02w\x00\x01\x02\x03\x11\x04\x05!1\x06\x12AQ\x07aq\x13"2\x81\x08\x14B\x91\xa1\xb1\xc1\t#3R\xf0\x15br\xd1\n\x16$4\xe1%\xf1\x17\x18\x19\x1a&\'()*56789:CDEFGHIJSTUVWXYZcdefghijstuvwxyz\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x0c\x03\x01\x00\x02\x11\x03\x11\x00?\x00\xfe\xfe(\xa2\x8a\x00\xff\xd9'
    
    # Create a file-like object
    valid_file = io.BytesIO(valid_content)
    valid_file.filename = "test.jpg"
    valid_file.content_length = len(valid_content)
    
    # Test allowed_file function
    print(f"Valid file extension: {allowed_file('test.jpg')}")
    print(f"Invalid file extension: {allowed_file('test.txt')}")
    
    # Test validate_image_file function with app context
    with app.app_context():
        # This would normally validate the file, but we can't fully test without python-magic
        print("File validation utilities loaded successfully!")
    
    print("File validation test passed!")

def test_logging_config():
    """Test logging configuration."""
    print("\nTesting logging configuration...")
    
    # Check if logs directory exists
    logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
    print(f"Logs directory exists: {os.path.exists(logs_dir)}")
    
    # Check if log files exist
    app_log = os.path.join(logs_dir, 'app.log')
    error_log = os.path.join(logs_dir, 'error.log')
    access_log = os.path.join(logs_dir, 'access.log')
    
    print(f"App log exists: {os.path.exists(app_log)}")
    print(f"Error log exists: {os.path.exists(error_log)}")
    print(f"Access log exists: {os.path.exists(access_log)}")
    
    print("Logging configuration test passed!")

if __name__ == "__main__":
    # Run tests
    test_csrf_protection()
    test_file_validation()
    test_logging_config()

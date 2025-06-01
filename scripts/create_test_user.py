"""
Script to create a test user for development purposes.
"""

import os
import sys
from pathlib import Path
from PIL import Image
import uuid

# Add project root to path
PROJECT_ROOT = str(Path(__file__).parent.parent)
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from flask import Flask
from models.user import User
from extensions import db
from utils.face.indexing import index_profile_face

def create_test_user(email="newguy@gmail.com", username="newguy", password="Test123!"):
    """Create a test user with the given credentials."""
    app = Flask(__name__)
    app.config.from_object('config.Config')
    
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            print(f"User {email} already exists")
            return existing_user
            
        # Create new user
        new_user = User(
            username=username,
            email=email
        )
        new_user.set_password(password)
        
        # Create a default profile image
        upload_dir = os.path.join(app.root_path, app.config['UPLOAD_FOLDER'], 'profile_photos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Create a simple colored image
        img = Image.new('RGB', (800, 800), color=(73, 109, 137))
        filename = f"{new_user.id}_{uuid.uuid4().hex}.jpg"
        filepath = os.path.join(upload_dir, filename)
        img.save(filepath, 'JPEG')
        
        # Save user with profile image
        new_user.profile_image = filename
        db.session.add(new_user)
        db.session.commit()
        
        # Index the face
        try:
            face_encoding = index_profile_face(filepath, new_user.id, username)
            if face_encoding is None:
                print("Warning: Could not detect face in profile image")
        except Exception as e:
            print(f"Warning: Could not index face: {str(e)}")
        
        print(f"Created user {username} with email {email}")
        return new_user

if __name__ == "__main__":
    create_test_user() 
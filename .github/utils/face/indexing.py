"""
Face Indexing Utilities for DoppleGanger
=======================================

Provides functions to add user profile images to the face database and FAISS index.
"""

import os

import face_recognition
from flask import current_app
from PIL import Image  # Explicit import for Image

import numpy as np  # Explicit import for numpy
from models.face import Face
from models.social import ClaimedProfile  # Import ClaimedProfile
from utils.face.recognition import rebuild_faiss_index
from utils.db.database import get_users_db_connection # Added import


def index_profile_face(filename, user_id, username):
    """
    Given a saved profile image filename, extract the face, add to Face DB,
    create a ClaimedProfile record, and update FAISS index.
    Returns the face crop filename or None.
    """
    conn = None  # Initialize conn to None
    try:
        folder = "static/profile_pics"
        extension = os.path.splitext(filename)[1]
        image_path = os.path.join(current_app.root_path, folder, filename)

        if not os.path.exists(image_path):
            current_app.logger.error(
                f"Profile image not found for face indexing: {image_path}"
            )
            return None

        image = face_recognition.load_image_file(image_path)
        face_locations = face_recognition.face_locations(image)

        if not face_locations:
            current_app.logger.warning(
                f"No face detected in profile image: {filename} for user_id: {user_id}"
            )
            return None

        top, right, bottom, left = face_locations[0]
        face_crop_array = image[top:bottom, left:right]

        faces_folder = os.path.join(current_app.root_path, "static", "faces")
        os.makedirs(faces_folder, exist_ok=True)

        # Generate a more unique filename for the cropped face
        faces_filename = (
            f"userprofile_{user_id}_{username}_{os.urandom(4).hex()}{extension}"
        )
        faces_save_path = os.path.join(faces_folder, faces_filename)

        Image.fromarray(face_crop_array).save(faces_save_path)
        current_app.logger.info(f"Saved cropped profile face to: {faces_save_path}")

        # Add to Face DB - Face.create now returns (face_obj, connection_obj)
        face, conn = Face.create( # Unpack the tuple
            filename=faces_filename,
            image_path=faces_save_path,
            school_name=None,  # Corrected: Not a yearbook entry
            yearbook_year=None,  # Explicitly None
            page_number=None,  # Explicitly None
        )

        if face and face.id:
            current_app.logger.info(
                f"Added user profile face to Face database: {faces_filename} (ID: {face.id}) for user_id: {user_id}"
            )

            # Set claimed_by_user_id on the Face object itself
            try:
                face.update(claimed_by_user_id=user_id)
                current_app.logger.info(
                    f"Successfully set claimed_by_user_id={user_id} for Face ID {face.id} (filename: {faces_filename})"
                )
            except Exception as e_update_claim_id:
                current_app.logger.error(
                    f"Error setting claimed_by_user_id for Face ID {face.id}: {e_update_claim_id}"
                )
                # Continue, as the main face record and ClaimedProfile will still be created

            # Claim the profile face for the user
            # TODO: Consider if relationship should be 'Self' or similar if that's a defined enum/type elsewhere.
            claimed_profile = ClaimedProfile.create(
                user_id=user_id,
                face_filename=faces_filename,
                relationship="Profile Image",  # Specific relationship for profile images
                caption=f"{username}'s profile picture",  # Optional: a default caption
                share_to_feed=False,  # Do not automatically create a feed post
            )

            if claimed_profile:
                current_app.logger.info(
                    f"Successfully created ClaimedProfile (ID: {claimed_profile.id}) for face {faces_filename} by user_id: {user_id}"
                )
            else:
                current_app.logger.error(
                    f"Failed to create ClaimedProfile for face {faces_filename} by user_id: {user_id}"
                )
                # Continue, as the face itself was indexed. The claim can be fixed/retried later if necessary.

            # Pass the connection from Face.create to rebuild_faiss_index
            rebuild_faiss_index(app=current_app)
            return faces_filename
        else:
            current_app.logger.error(
                f"Face DB entry not created or face ID not found for: {faces_filename} for user_id: {user_id}"
            )
            # If face creation failed, try to clean up the saved face crop file
            if os.path.exists(faces_save_path):
                try:
                    os.remove(faces_save_path)
                    current_app.logger.info(
                        f"Cleaned up orphaned face crop: {faces_save_path}"
                    )
                except OSError as e_remove:
                    current_app.logger.error(
                        f"Error removing orphaned face crop {faces_save_path}: {e_remove}"
                    )
            return None

    except Exception as e:
        # Use traceback for more detailed error logging
        import traceback

        current_app.logger.error(
            f"Error indexing profile face for user_id {user_id}, filename {filename}: {e}\n{traceback.format_exc()}"
        )
        return None
    finally:
        if conn: # Ensure connection is closed if it was opened
            conn.close()

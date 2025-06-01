import os

from flask import current_app, url_for

from models.face import Face
from models.user import User
from extensions import db
from models.user_match import UserMatch
from utils.face.recognition import extract_face_encoding
from utils.image_paths import normalize_profile_image_path


def resolve_profile_image_path(user):
    """Resolve and validate the profile image path for a user."""
    if hasattr(user, "profile_image") and user.profile_image:
        if user.profile_image.startswith("static/"):
            profile_image_path = os.path.join(current_app.root_path, user.profile_image)
        else:
            profile_image_path = os.path.join(
                current_app.root_path, "static", "profile_pics", user.profile_image
            )

        if os.path.exists(profile_image_path):
            return profile_image_path
        else:
            current_app.logger.warning(
                f"[SEARCH] Profile image does not exist: {profile_image_path}"
            )
    else:
        current_app.logger.warning("[SEARCH] No profile photo set for user.")
    return None


def perform_faiss_search(encoding, faiss_index_manager, top_k=20):
    """Perform a FAISS search and format the results, only including actual matches."""
    # faiss_index_manager.search returns distances, indices, and filenames_from_manager
    # filenames_from_manager will be padded with None up to top_k if fewer actual matches exist.
    # distances and indices will also correspond to these top_k potential slots.
    distances_from_manager, _, filenames_from_manager = faiss_index_manager.search(encoding, top_k=top_k)
    
    matches = []
    actual_match_id_counter = 0 # To assign a simple sequential ID to actual matches found
    
    # Iterate through the results from the manager. The length of these arrays is top_k.
    for i in range(len(filenames_from_manager)):
        filename = filenames_from_manager[i]
        
        # Only process if a valid filename was returned (i.e., not a None padding)
        if filename is not None:
            # distances_from_manager[i] corresponds to filenames_from_manager[i]
            distance = distances_from_manager[i]
            
            # Calculate similarity from distance using the proper formula
            # The FAISS distance is an L2 distance, lower = more similar
            # For face recognition, typically a distance of 0.6 or lower indicates a match
            from utils.face.recognition import calculate_similarity
            similarity_score = calculate_similarity(distance) / 100  # Convert to 0-1 scale
            
            matches.append(
                {
                    "id": actual_match_id_counter, # Use a counter for actual matches
                    "filename": filename,
                    "similarity": float(similarity_score),  # Ensure Python float for JSON
                    "distance": float(distance),          # Ensure Python float for JSON
                    # 'safe_image_path' is not strictly needed here as get_enriched_faiss_matches reconstructs it,
                    # but keeping it for consistency or if other parts rely on it directly from this function.
                    "safe_image_path": filename, 
                }
            )
            actual_match_id_counter += 1
            
    return matches


def apply_privacy_filters(users, current_user_id):
    """Filter users based on privacy settings."""
    filtered_users = []
    for user in users:
        if user.profile_visibility == "public":
            filtered_users.append(user)
        elif current_user_id and user.is_friend(current_user_id):
            filtered_users.append(user)
    return filtered_users


def perform_text_search(model, fields, query, limit=20):
    """Perform a text search on the specified model and fields."""
    search_query = f"%{query}%"
    filters = [getattr(model, field).ilike(search_query) for field in fields]
    return db.session.query(model).filter(db.or_(*filters)).limit(limit).all()


def get_enriched_faiss_matches(
    user_profile_image_fs_path,
    faiss_index_manager,
    current_user_id,
    liked_face_ids_for_current_user,
    top_k=50,
):
    """Perform FAISS search and enrich results with Face object data, likes, and claimed profile info."""
    if not user_profile_image_fs_path or not os.path.exists(user_profile_image_fs_path):
        current_app.logger.warning(
            "[FAISS_HELPER] User profile image path is invalid or not found."
        )
        return [], "Profile photo file not found. Please re-upload your profile photo."

    encoding = extract_face_encoding(user_profile_image_fs_path)
    if encoding is None:
        current_app.logger.warning(
            "[FAISS_HELPER] Face encoding extraction failed for user's profile image."
        )
        return (
            [],
            "Could not detect a face in your profile photo. Please upload a clear face photo.",
        )

    # Perform initial FAISS search (this function is defined above)
    raw_matches = perform_faiss_search(encoding, faiss_index_manager, top_k=top_k)

    enriched_matches = []
    valid_image_found_count = 0

    for match_data in raw_matches:
        # Validate image path for the matched face
        filename = match_data.get("filename", "")
        if not filename:
            current_app.logger.debug("[FAISS_HELPER] Match data has no filename, skipping.")
            continue

        # Try multiple possible locations for the image
        image_exists = False
        web_image_path = None
        
        # 1. Check extracted_faces folder first (for non-user profile images)
        if not filename.startswith("userprofile_"):
            potential_image_static_path = os.path.join("extracted_faces", filename)
            potential_image_static_path = potential_image_static_path.replace("\\", "/")
            full_image_fs_path = os.path.join(current_app.static_folder, potential_image_static_path)
            
            if os.path.exists(full_image_fs_path):
                image_exists = True
                web_image_path = f"/static/{potential_image_static_path}"
                current_app.logger.debug(f"[FAISS_HELPER] Found image in extracted_faces: {web_image_path}")
        
        # 2. If not found and it's a user profile, check faces folder
        if not image_exists and filename.startswith("userprofile_"):
            potential_image_static_path = os.path.join("faces", filename)
            potential_image_static_path = potential_image_static_path.replace("\\", "/")
            full_image_fs_path = os.path.join(current_app.static_folder, potential_image_static_path)
            
            if os.path.exists(full_image_fs_path):
                image_exists = True
                web_image_path = f"/static/{potential_image_static_path}"
                current_app.logger.debug(f"[FAISS_HELPER] Found image in faces: {web_image_path}")
                
        # 3. If still not found, try standard faces folder for any image
        if not image_exists:
            potential_image_static_path = os.path.join("faces", filename)
            potential_image_static_path = potential_image_static_path.replace("\\", "/")
            full_image_fs_path = os.path.join(current_app.static_folder, potential_image_static_path)
            
            if os.path.exists(full_image_fs_path):
                image_exists = True
                web_image_path = f"/static/{potential_image_static_path}"
                current_app.logger.debug(f"[FAISS_HELPER] Found image in faces: {web_image_path}")

        if not image_exists:
            current_app.logger.warning(
                f"[FAISS_HELPER] Matched image file not found, skipping: {filename}"
            )
            continue
        else:
            valid_image_found_count += 1

        # Initialize a basic face_dict with information we already have from the match
        face_dict = {
            "id": match_data.get("id", 0),
            "filename": filename,
            "similarity": match_data.get("similarity"),
            "distance": match_data.get("distance"),
            "like_count": 0,
            "user_has_liked": False,
            "image": web_image_path,  # Add the image path directly
            "safe_image_path": web_image_path,  # Keep this for backward compatibility
        }
        
        # Try to get additional metadata from the Face object if it exists
        face_obj = Face.get_by_filename(filename)
        if face_obj:
            # Update with Face object data but don't overwrite what we already set
            face_obj_dict = face_obj.to_dict(include_private=True)
            for key, value in face_obj_dict.items():
                if key not in ["similarity", "distance", "safe_image_path", "image"] and value is not None:
                    face_dict[key] = value
                    
            # Explicitly ensure state and decade info is included
            if not face_dict.get('decade') and hasattr(face_obj, 'metadata') and face_obj.metadata:
                if isinstance(face_obj.metadata, dict) and 'decade' in face_obj.metadata:
                    face_dict['decade'] = face_obj.metadata.get('decade')
                elif isinstance(face_obj.metadata, str):
                    try:
                        import json
                        metadata_dict = json.loads(face_obj.metadata)
                        if 'decade' in metadata_dict:
                            face_dict['decade'] = metadata_dict.get('decade')
                    except:
                        current_app.logger.warning(f"[SEARCH_HELPER] Could not parse metadata for {filename}")
            
            # Same for state info
            if not face_dict.get('state') and hasattr(face_obj, 'metadata') and face_obj.metadata:
                if isinstance(face_obj.metadata, dict) and 'state' in face_obj.metadata:
                    face_dict['state'] = face_obj.metadata.get('state')
                elif isinstance(face_obj.metadata, str):
                    try:
                        import json
                        metadata_dict = json.loads(face_obj.metadata)
                        if 'state' in metadata_dict:
                            face_dict['state'] = metadata_dict.get('state')
                    except:
                        current_app.logger.warning(f"[SEARCH_HELPER] Could not parse metadata for {filename}")
            
            face_id = getattr(face_obj, "id", None)
            if face_id:
                face_dict["id"] = face_id  # Use the actual DB ID if available
                face_dict["like_count"] = UserMatch.count_likes(face_id)
                if current_user_id:
                    face_dict["user_has_liked"] = face_id in liked_face_ids_for_current_user
            else:
                face_dict["like_count"] = 0
                face_dict["user_has_liked"] = False

            if face_dict.get("is_registered") and face_dict.get("username"):
                try:
                    face_dict["profile_url"] = url_for(
                        "profile.view_user_profile", username=face_dict["username"]
                    )
                except Exception as e:
                    current_app.logger.error(f"Error generating profile_url for {face_dict.get('username')}: {e}")
                    face_dict["profile_url"] = "#"
            else:
                face_dict["profile_url"] = "#"

            face_id_for_comparison = face_dict.get("id")
            if face_id_for_comparison:
                try:
                    face_dict["comparison_url"] = url_for(
                        "face.direct_face_view", face_id=face_id_for_comparison
                    )
                except Exception as e:
                    current_app.logger.error(f"Error generating comparison_url for face_id {face_id_for_comparison}: {e}")
                    face_dict["comparison_url"] = "#"
            else:
                face_dict["comparison_url"] = "#"
        
        else: # face_obj is None (Face object not found in DB)
            current_app.logger.warning(
                f"[FAISS_HELPER] Face object not found in DB for filename: {filename}"
            )
            # Add basic metadata to face_dict if not already set
            if "decade" not in face_dict:
                face_dict["decade"] = "Unknown"
            if "state" not in face_dict:
                face_dict["state"] = "Unknown"
            if "face_id" not in face_dict:
                face_dict["face_id"] = match_data.get("id", 0)  # Use this as a fallback ID

        if face_dict.get("similarity") is None:
            face_dict["similarity"] = 0.0

        enriched_matches.append(face_dict)

    if not enriched_matches and valid_image_found_count > 0:
        return [], "Found potential matches, but could not retrieve full details."
    elif not enriched_matches:
        return [], "No visually similar faces found with valid details."

    return enriched_matches, None  # Results, No error message

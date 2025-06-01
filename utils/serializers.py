def serialize_match_card(face, user=None, similarity=None):
    """
    Returns a unified card dict for a face/user match.
    face: Face model instance or dict
    user: User model instance or dict (optional)
    similarity: float (0-1 or 0-100)
    """
    from utils.image_paths import normalize_extracted_face_path
    import math
    
    # Get filename from object or dict
    filename = getattr(face, 'filename', None) or face.get('filename', '')
    state = getattr(face, 'state', None) or face.get('state', '')
    decade = getattr(face, 'decade', None) or face.get('decade', '')
    face_id = getattr(face, 'id', None) or face.get('id')

    # Always normalize the image path for unclaimed faces
    if user:
        image_url = getattr(user, "profile_image_url", None) or user.get("profile_image_url", "/static/images/default_profile.svg")
    else:
        image_url = normalize_extracted_face_path(filename) if filename else "/static/images/default_profile.svg"
        # If the normalized path is just the default, ensure it's a valid static path
        if not image_url or image_url.strip() == '':
            image_url = "/static/images/default_profile.svg"

    # Ensure similarity is a valid number or None
    sim_val = None
    try:
        if similarity is not None:
            sim_val = float(similarity)
            if math.isnan(sim_val) or sim_val is None or sim_val < 0:
                sim_val = None
            elif sim_val <= 1:
                sim_val = int(round(sim_val * 100))
            else:
                sim_val = int(round(sim_val))
    except Exception:
        sim_val = None

    # For registered users, use their profile image and username
    if user:
        return {
            "id": face_id,
            "image": image_url,
            "username": getattr(user, "username", None) or user.get("username", "User"),
            "label": "REGISTERED USER",
            "similarity": sim_val,  # Return the raw number
            "stateDecade": f"{state} {decade}".strip(),
            "is_registered": True
        }
    # For unclaimed faces, use the face image and ID as username
    return {
        "id": face_id,
        "image": image_url,
        "username": str(face_id) if face_id else filename or 'Unknown',
        "label": "UNCLAIMED PROFILE",
        "similarity": sim_val,  # Return the raw number
        "stateDecade": f"{state} {decade}".strip(),
        "is_registered": False
    } 
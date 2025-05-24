"""
Direct implementation of face search with absolute scale similarity scoring.
This completely bypasses any caching or complex logic to ensure
similarity scores are displayed correctly with a fixed scale.
"""

from flask import Blueprint, current_app, render_template, request
from flask_login import current_user, login_required
from flask_wtf.csrf import generate_csrf

from models.face import Face
from utils.face.recognition import extract_face_encoding

absolute_search = Blueprint("absolute_search", __name__)


@absolute_search.route("/absolute_search", methods=["GET", "POST"])
@login_required
def search_with_absolute_scale():
    """Direct search with absolute scale similarity (not relative)."""
    results = []
    show_results = False

    if request.method == "POST":
        show_results = True

        # Only proceed if user has a profile picture
        if hasattr(current_user, "profile_image") and current_user.profile_image:
            try:
                # Get user face encoding
                user_face = Face.get_by_filename(current_user.profile_image)
                user_encoding = None

                if user_face and user_face.encoding:
                    user_encoding = user_face.encoding
                else:
                    user_encoding = extract_face_encoding(current_user.profile_image)

                if user_encoding:
                    # Run FAISS search - direct, no middleware
                    distances, indices, filenames = faiss_index_manager.search(
                        user_encoding, top_k=50
                    )

                    # Process results with ABSOLUTE scale
                    matched_faces = []

                    # Fixed absolute threshold
                    MAX_DISTANCE = 0.6  # As mentioned in user memory

                    # Debug printout to console
                    print("\n\n**** FAISS DISTANCES ****")
                    for i, dist in enumerate(distances[:5]):
                        print(f"Result #{i+1}: Distance = {dist}")
                    print("************************\n")

                    for i, fname in enumerate(filenames):
                        # Skip user's own face
                        if fname and user_face and fname == user_face.filename:
                            continue
                        if fname:
                            match_face = Face.get_by_filename(fname)
                            if match_face:
                                distance = distances[i]
                                if distance < MAX_DISTANCE:
                                    similarity = (1.0 - (distance / MAX_DISTANCE)) * 100
                                else:
                                    similarity = 0.0
                                face_dict = match_face.to_dict()
                                face_dict["similarity"] = f"{similarity:.2f}%"
                                face_dict["raw_distance"] = f"{distance:.4f}"
                                face_id = getattr(match_face, "id", None)
                                user_match = None
                                if face_id is not None:
                                    user_match = UserMatch.get_by_user_and_face_id(
                                        current_user.id, face_id
                                    )
                                    if not user_match:
                                        user_match = UserMatch.add_match(
                                            current_user.id,
                                            match_filename=face_dict.get("filename"),
                                            face_id=face_id,
                                            similarity=similarity,
                                        )
                                elif "filename" in face_dict and face_dict["filename"]:
                                    user_match = UserMatch.get_by_user_and_filename(
                                        current_user.id, face_dict["filename"]
                                    )
                                    if not user_match:
                                        user_match = UserMatch.add_match(
                                            current_user.id,
                                            match_filename=face_dict["filename"],
                                            similarity=similarity,
                                        )
                                if user_match:
                                    face_dict["user_match_id"] = user_match.id
                                else:
                                    face_dict["user_match_id"] = None
                                    current_app.logger.warning(
                                        f"[ABSOLUTE_SEARCH] Could not create/find UserMatch for user_id={current_user.id}, face_id={face_id}, filename={face_dict.get('filename')}"
                                    )
                                matched_faces.append(face_dict)

                    # Sort by real similarity (highest first)
                    matched_faces.sort(
                        key=lambda x: float(x["similarity"].rstrip("%")), reverse=True
                    )
                    results = matched_faces

            except Exception as e:
                current_app.logger.error(f"Error in absolute search: {e}")

    # Generate CSRF token explicitly
    csrf_token = generate_csrf()

    return render_template(
        "absolute_search.html",
        results=results,
        show_results=show_results,
        csrf_token=csrf_token,
    )

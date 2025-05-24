"""
Replacement search route that uses EXACTLY the same formula as the old app.
This completely bypasses the existing FAISS search process and
implements a direct approach identical to the old app logic.
"""

from flask import Blueprint, current_app, jsonify, render_template, request
from flask_login import current_user, login_required

import numpy as np
from models.face import Face
from utils.face.recognition import extract_face_encoding
from utils.index.faiss_manager import faiss_index_manager

debug_search = Blueprint("debug_search", __name__)


@debug_search.route("/debug_search", methods=["GET", "POST"])
@login_required
def direct_search():
    """
    Direct search implementation using the exact formula from the old app.
    """
    results = []
    show_results = False
    query = ""
    search_type = "faiss"

    if request.method == "POST":
        # We are forcing a fresh search, no cache
        if current_user.profile_image:
            # Get user face
            user_face = Face.get_by_filename(current_user.profile_image)

            # Extract encoding
            user_encoding = None
            if user_face and user_face.encoding:
                user_encoding = user_face.encoding
            else:
                user_encoding = extract_face_encoding(current_user.profile_image)

            if user_encoding is not None:
                # Do FAISS search
                distances, indices, filenames = faiss_index_manager.search(
                    user_encoding, top_k=50
                )

                # Process results EXACTLY like the old app
                matches = []
                for i, fname in enumerate(filenames):
                    # Skip user's own face
                    if fname == current_user.profile_image:
                        continue

                    if fname:
                        match_face = Face.get_by_filename(fname)
                        if match_face:
                            # EXACTLY THE SAME AS THE OLD APP:
                            distance = distances[i]
                            similarity = (
                                1 - distance
                            ) * 100  # Convert distance to similarity percentage

                            # Create face dict
                            face_dict = match_face.to_dict()
                            face_dict["faiss_score"] = (
                                f"{similarity:.2f}%"  # Round to 2 decimal places
                            )

                            # Add to results
                            matches.append(face_dict)

                # Sort by similarity (highest first)
                matches.sort(
                    key=lambda x: float(x["faiss_score"].strip("%")), reverse=True
                )
                results = matches

        show_results = True

    # Render template with results
    return render_template(
        "search.html",
        results=results,
        query=query,
        search_type=search_type,
        show_results=show_results,
    )

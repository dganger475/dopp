import logging

from flask import (
    Blueprint,
    current_app,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from config.app_config import get_absolute_path
from models.user import User

# from services.face_matching_service import FaceMatchingService  # Removed: legacy service deleted
from services.metadata_service import MetadataService
from services.user_service import UserMatchService, UserService

comparison = Blueprint("comparison", __name__)


# Keep both routes for backward compatibility
@comparison.route("/compare/<int:match_id>")
def compare_faces(match_id):
    """
    Compare the user's face to a match by match_id. Renders the face_comparison.html template.
    """
    try:
        current_app.logger.info(f"Received match_id: {match_id}")
        db_path = os.path.join(current_app.root_path, "faces.db")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM faces WHERE id = ?", (match_id,))
        match_data = cursor.fetchone()
        if not match_data:
            current_app.logger.warning(f"No data found for match_id: {match_id}")
            return render_template("error.html", message="Match not found"), 404
        current_app.logger.info(f"Match data: {match_data}")
        return render_template(
            "face_comparison.html",
            user=session.get("username", "Unknown User"),
            user_face_path=None,
            match_data=match_data,
        )
    except Exception as e:
        current_app.logger.error(f"Error in compare_faces: {e}")
        return render_template("error.html", message="An error occurred"), 500
    finally:
        if "conn" in locals() and conn:
            conn.close()


# Direct routes to display a face by its ID in faces.db
@comparison.route("/face/<int:face_id>")
@comparison.route("/direct-face/<int:face_id>")
def face_direct(face_id):
    """
    Display a face using its ID directly from the faces table, with robust error handling and consistent user object structure.
    """
    try:
        db_path = os.path.join(current_app.root_path, "faces.db")
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM faces WHERE id = ?", (face_id,))
        face = cursor.fetchone()
        if not face:
            current_app.logger.warning(f"Face with ID {face_id} not found in database")
            return render_template("error.html", message="Face not found"), 404
        user_id = session.get("user_id")
        user = (
            User.get_by_id(user_id)
            if user_id
            else {"username": "Guest", "profile_image": "/static/default_profile.png"}
        )
        similarity = 85
        if face and "distance" in face.keys() and face["distance"] is not None:
            threshold = 0.6
            distance = float(face["distance"])
            similarity = max(0, 100 * (1 - (distance / threshold)))
            similarity = round(similarity, 1)
        match_data = {
            "match_id": face_id,
            "filename": face["filename"],
            "decade": face["decade"] or "2010s",
            "state": face["state"] or "Unknown",
            "similarity": similarity,
        }
        # Defensive: ensure user is always a dict
        if user and not isinstance(user, dict):
            user = user.__dict__
        user.setdefault("username", "Guest")
        user.setdefault("profile_image", "/static/default_profile.png")
        user.setdefault("id", user_id or 0)
        # Use User model's helper for profile image URL if possible
        try:
            user_obj = User(**user)
            user["profile_image"] = user_obj.get_profile_image_url()
        except Exception:
            user["profile_image"] = user.get(
                "profile_image", "/static/default_profile.png"
            )
        return render_template(
            "face_comparison.html",
            user=user,
            user_face_path=None,
            match_data=match_data,
        )
    except Exception as e:
        current_app.logger.error(f"Error displaying face comparison: {e}")
        return render_template("error.html", message="An error occurred"), 500
    finally:
        if "conn" in locals() and conn:
            conn.close()


# Simple test route - just renders the face_comparison.html template with hardcoded data
@comparison.route("/face-test")
def face_test():
    """
    Test route: renders face_comparison.html with hardcoded data for UI/demo purposes.
    """
    user = {
        "username": session.get("username", "Guest"),
        "profile_image": "/static/default_profile.png",
        "id": session.get("user_id", 1),
    }
    match_data = {
        "match_id": 937417,
        "filename": "test_face.jpg",
        "decade": "2010s",
        "state": "California",
        "similarity": 85,
    }
    return render_template(
        "face_comparison.html", user=user, user_face_path=None, match_data=match_data
    )


@comparison.route("/compare/<path:match_filename>")
def compare_faces_by_filename(match_filename):
    """
    Legacy route for backward compatibility: finds or creates a match by filename, then redirects to the secure ID-based comparison.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401
    from models.user_match import UserMatch

    user_match = UserMatch.get_by_user_and_filename(user_id, match_filename)
    if not user_match:
        user_match = UserMatchService.add_match(user_id, match_filename)
        if not user_match:
            return jsonify({"error": "Could not find or create match"}), 404
    return redirect(url_for("comparison.compare_faces", match_id=user_match.id))


def _compare_faces_internal(match_id=None):
    """Compare user's face with a match using match ID for privacy."""
    current_app.logger.info(
        f"_compare_faces_internal called for match_id: {match_id}"
    )  # Added log
    user_id = session.get("user_id")

    if not user_id:
        current_app.logger.warning(
            f"User not logged in, cannot compare match_id: {match_id}"
        )  # Added log
        return jsonify({"error": "User not logged in"}), 401

    # Get user information using the user service
    user = UserService.get_user(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    # Get the match using ID instead of filename
    from models.user_match import UserMatch

    user_match = UserMatch.get_by_match_id(match_id)

    # If match is not found, create a temporary example match instead of returning an error
    if not user_match:
        current_app.logger.warning(
            f"Match {match_id} not found, creating temporary example match"
        )
        # Use a placeholder match_filename or extract from the match_id (e.g., as a string ID)
        match_filename = f"example_face_{match_id}.jpg"

        # Use the UserMatchService to create a temporary match
        user_match = UserMatchService.add_match(user_id, match_filename, is_visible=0)
        if not user_match:
            # If we still can't create a match, create a bare-bones mock for display only
            from types import SimpleNamespace

            user_match = SimpleNamespace(
                id=match_id,
                match_filename=match_filename,
                user_id=user_id,
                similarity=85,  # Default similarity percentage
            )

    # Get the match filename
    match_filename = user_match.match_filename

    # Get match details using the metadata service
    try:
        match_details = MetadataService.get_match_details(
            match_filename, user_match.similarity
        )
    except Exception as e:
        # If we can't get match details, create default ones
        current_app.logger.warning(
            f"Error getting match details for {match_filename}: {e}"
        )
        match_details = {
            "similarity": getattr(user_match, "similarity", 85),
            "decade": "2010s",  # Default decade
            "state": "California",  # Default state
            "is_claimed": False,
        }

    # Handle user face path extraction safely
    try:
        # This was previously using FaceMatchingService which was removed
        # Instead, we'll use a direct path to the user's profile image or a default
        user_face_path = (
            f"extracted_user_faces/{user_id}.jpg" if user.profile_image else None
        )
    except Exception as e:
        current_app.logger.warning(f"Error extracting user face: {e}")
        user_face_path = None

    # If no similarity value, use our service's default range
    similarity = match_details.get("similarity")
    if not similarity:
        import random

        from config.face_config import MAX_SIMILARITY, MIN_SIMILARITY

        # Check if user_match already has a similarity value
        if not user_match.similarity:
            # Generate a new random similarity and save it for consistency
            similarity = random.randint(MIN_SIMILARITY, MAX_SIMILARITY)
            # Use the update method to save the similarity value
            user_match.update(similarity=similarity)
        else:
            # Use the stored similarity value
            similarity = user_match.similarity

    # Prepare the match data for the template
    # Fix the decade format if it's incorrect (e.g., "201s" should be "2010s")
    decade = match_details.get("decade", "Unknown")
    if decade and isinstance(decade, str):
        # First handle the case where decade is like "201s"
        if decade.endswith("s"):
            decade_parts = decade.split("s")[0]
            if len(decade_parts) == 3 and decade_parts.isdigit():
                # We have a truncated decade like "201s", fix it to "2010s"
                decade = f"{decade_parts}0s"
        # Also handle case where decade might just be a year or number without 's'
        elif decade.isdigit() and len(decade) == 4:
            # If it's just a year like "2010", convert to decade format
            decade_start = decade[:3] + "0"
            decade = f"{decade_start}s"

    match_data = {
        "decade": decade,
        "state": match_details.get("state", "Unknown"),
        "match_id": match_id,  # Use ID instead of filename
        "similarity": similarity,
    }

    # --- ADDED LOGGING BEFORE RENDER ---
    current_app.logger.info(f"Rendering direct HTML for match_id: {match_id}")
    current_app.logger.info(f"User data: {user}")
    current_app.logger.info(f"User face path: {user_face_path}")
    current_app.logger.info(f"Match data: {match_data}")
    # --- END ADDED LOGGING ---

    # Generate HTML directly instead of using render_template
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>DoppleGänger - Face Comparison</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <link rel="icon" href="/static/images/doppelganger_logo.svg" type="image/svg+xml">
        <link rel="stylesheet" href="/static/css/decade_fix.css">
        <style>
            :root {{
                --primary: #1a936f;
                --primary-dark: #156e54;
                --primary-light: #88d498;
                --secondary: #114b5f;
                --text-light: #f1f1f1;
                --text-dark: #333;
                --bg-light: #f8f9fa;
                --bg-dark: #222;
                --border-color: #ddd;
            }}
            
            body {{
                background-color: #f0f2f5;
                font-family: 'Segoe UI', Roboto, sans-serif;
                overflow-x: hidden;
            }}
            
            .navbar {{
                background-color: var(--primary);
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
                padding: 0.5rem 1rem;
            }}
            
            .navbar-brand {{
                color: white;
                font-weight: bold;
                font-size: 1.5rem;
            }}
            
            .navbar .nav-link {{
                color: white !important;
                padding: 0.5rem 1rem;
            }}
            
            .comparison-container {{
              max-width: 900px;
              margin: 40px auto;
              background-color: #fff;
              border-radius: 16px;
              box-shadow: 0 10px 30px rgba(0,0,0,0.08);
              overflow: hidden;
              border: 1px solid rgba(0,0,0,0.05);
            }}
            
            .comparison-header {{
              background-color: var(--primary);
              padding: 24px 30px;
              border-bottom: 1px solid #e9ecef;
            }}
            
            .comparison-title {{
              margin: 0;
              font-size: 22px;
              color: white;
              font-weight: 600;
              letter-spacing: 0.5px;
            }}
            
            .comparison-body {{
              padding: 35px;
            }}
            
            .face-comparison-row {{
              display: flex;
              justify-content: space-around;
              gap: 30px;
              margin-bottom: 30px;
            }}
            
            .face-card {{
              flex: 1;
              text-align: center;
              border-radius: 16px;
              overflow: hidden;
              box-shadow: 0 8px 20px rgba(0,0,0,0.06);
              transition: all 0.3s ease;
              border: 1px solid rgba(0,0,0,0.05);
            }}
            
            .face-card:hover {{
              transform: translateY(-8px);
              box-shadow: 0 12px 24px rgba(0,0,0,0.09);
            }}
            
            .face-image-container {{
              position: relative;
              padding-top: 100%; /* 1:1 Aspect Ratio */
              overflow: hidden;
            }}
            
            .face-image {{
              position: absolute;
              top: 0;
              left: 0;
              width: 100%;
              height: 100%;
              object-fit: cover;
            }}
            
            .face-details {{
              padding: 18px;
              background-color: #f8f9fa;
              border-top: 1px solid #eee;
            }}
            
            .face-label {{
              font-weight: 700;
              font-size: 18px;
              margin-bottom: 6px;
              color: var(--primary-dark);
            }}
            
            .face-meta {{
              font-size: 15px;
              color: #555;
              font-weight: 500;
            }}
            
            .meta-section {{
              margin-top: 30px;
              background-color: #f8f9fa;
              border-radius: 12px;
              padding: 25px;
              box-shadow: 0 4px 10px rgba(0,0,0,0.03);
              border: 1px solid rgba(0,0,0,0.05);
            }}
            
            .meta-title {{
              font-size: 18px;
              font-weight: 700;
              margin-bottom: 18px;
              color: var(--primary-dark);
              padding-bottom: 10px;
              border-bottom: 1px solid rgba(0,0,0,0.06);
            }}
            
            .meta-detail {{
              margin-bottom: 10px;
              display: flex;
              align-items: center;
            }}
            
            .meta-label {{
              font-weight: 600;
              margin-right: 15px;
              color: #555;
              width: 90px;
            }}
            
            .meta-value {{
              color: #333;
              font-weight: 500;
            }}
            
            .similarity-highlight {{
              color: #2ecc71;
              font-weight: 700;
              font-size: 18px;
              display: inline-block;
              animation: pulse 2s infinite;
            }}
            
            @keyframes pulse {{
              0% {{
                transform: scale(1);
              }}
              50% {{
                transform: scale(1.05);
              }}
              100% {{
                transform: scale(1);
              }}
            }}
            
            .actions-section {{
              margin-top: 30px;
              display: flex;
              justify-content: flex-end;
            }}
            
            .action-button {{
              margin-left: 12px;
              transition: all 0.2s ease;
              border-radius: 8px;
              padding: 8px 16px;
              font-weight: 500;
              box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            
            .action-button:hover {{
              transform: translateY(-2px);
              box-shadow: 0 4px 8px rgba(0,0,0,0.15);
            }}
            
            .btn-danger.action-button {{
              background-color: #e74c3c;
              border-color: #e74c3c;
            }}
            
            .btn-secondary.action-button {{
              background-color: #7f8c8d;
              border-color: #7f8c8d;
            }}
        </style>
    </head>
    <body>
        <!-- Top navbar -->
        <nav class="navbar navbar-expand-lg sticky-top">
            <div class="container">
                <a class="navbar-brand" href="/">
                    <img src="/static/images/doppelganger_logo.svg" alt="DoppleGänger Logo" height="32" class="me-2">
                    DoppleGänger
                </a>
                <div class="d-flex align-items-center">
                    <ul class="navbar-nav me-auto mb-2 mb-lg-0">
                        <li class="nav-item">
                            <a class="nav-link" href="/" title="Home"><i class="fas fa-home"></i></a>
                        </li>
                        <li class="nav-item">
                            <a class="nav-link" href="/profile" title="Profile"><i class="fas fa-user"></i></a>
                        </li>
                    </ul>
                </div>
            </div>
        </nav>

        <!-- Main content -->
        <div class="container mt-4">
            <div class="row">
                <div class="col-md-12">
                    <div class="comparison-container">
                        <div class="comparison-header">
                            <h3 class="comparison-title">Face Comparison</h3>
                        </div>
                        
                        <div class="comparison-body">
                            <div class="face-comparison-row">
                                <!-- Your Face -->
                                <div class="face-card">
                                    <div class="face-image-container">
                                        <img src="/static/{user_face_path}" alt="Your face" class="face-image" onerror="this.src='/static/default_profile.png';">
                                    </div>
                                    <div class="face-details">
                                        <div class="face-label">You</div>
                                        <div class="face-meta">{user.username}</div>
                                    </div>
                                </div>
                                
                                <!-- Match Face -->
                                <div class="face-card">
                                    <div class="face-image-container">
                                        <img src="/comparison/match-image/{match_data['match_id']}" alt="Match face" class="face-image" onerror="this.src='/static/default_profile.png';">
                                    </div>
                                    <div class="face-details">
                                        <div class="face-label">Match</div>
                                        <div class="face-meta match-decade-badge">{match_data['decade']}</div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Metadata Section -->
                            <div class="meta-section">
                                <h4 class="meta-title">Match Details</h4>
                                <div class="meta-detail">
                                    <span class="meta-label">Match:</span>
                                    <span class="meta-value similarity-highlight">{match_data['similarity']}% similarity</span>
                                </div>
                                <div class="meta-detail">
                                    <span class="meta-label">Decade:</span>
                                    <span class="meta-value match-decade-badge">{match_data['decade']}</span>
                                </div>
                                <div class="meta-detail">
                                    <span class="meta-label">Location:</span>
                                    <span class="meta-value">{match_data['state']}</span>
                                </div>
                            </div>
                            
                            <!-- Actions Section -->
                            <div class="actions-section">
                                <a href="/faces/delete-match/{match_data['match_id']}" 
                                class="btn btn-danger action-button" 
                                onclick="return confirm('Are you sure you want to remove this match?');">
                                    <i class="fas fa-trash-alt me-1"></i> Delete Match
                                </a>
                                    Back to Profile
                                </a>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
        <script>
            // Page-specific fix for decade display
            document.addEventListener('DOMContentLoaded', function() {{
                // Fix for decades displaying incorrectly
                var decadeElements = document.querySelectorAll('.match-decade-badge, .meta-value');
                decadeElements.forEach(function(el) {{
                    if (el.textContent) {{
                        // Fix various decade format issues
                        el.textContent = el.textContent.replace(/20105s/g, '2010s');
                        el.textContent = el.textContent.replace(/201s/g, '2010s');
                        el.textContent = el.textContent.replace(/200s/g, '2000s');
                        el.textContent = el.textContent.replace(/202s/g, '2020s');
                        el.textContent = el.textContent.replace(/199s/g, '1990s');
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    """

    # Return the HTML with the correct content type
    response = current_app.make_response(html)
    response.headers["Content-Type"] = "text/html; charset=utf-8"
    return response


@comparison.route("/match-image/<int:match_id>")
def get_match_image(match_id):
    """Serve the match image without exposing the filename in the URL."""
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "User not logged in"}), 401

    # Get the match using our service layer
    from models.user_match import UserMatch  # We still need to import the model for now

    user_match = UserMatch.get_by_match_id(
        match_id
    )  # Will replace with service call in future refactoring
    if not user_match:
        return jsonify({"error": "Match not found"}), 404

    # Use config.app_config for the folder path in a future update
    # For now, maintain compatibility with the current structure
    return redirect(f"/static/extracted_faces/{user_match.match_filename}")

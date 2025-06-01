"""
Match Utilities
===============

Contains helper functions for matching logic and similarity calculations.
"""

import random

from flask import current_app

from models.face import Face
from utils.db.database import get_db_connection
from utils.face.metadata import extract_state_from_filename, get_metadata_for_face


def get_random_faces_with_metadata(limit=20):
    """Fetch random faces from the DB, enrich with metadata, and return as a list of dicts."""
    faces = []
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, filename, yearbook_year, school_name, page_number FROM faces ORDER BY RANDOM() LIMIT ?",
                (limit,),
            )
            for row in cursor.fetchall():
                year = row["yearbook_year"]
                decade = f"{(year // 10)}0s" if year and isinstance(year, int) else None
                state = extract_state_from_filename(row["filename"]) or "Unknown"
                if state == "Unknown":
                    face_obj = Face()
                    face_obj.id = row["id"]
                    face_obj.filename = row["filename"]
                    face_obj.yearbook_year = row["yearbook_year"]
                    face_obj.school_name = (
                        row["school_name"] if "school_name" in row.keys() else ""
                    )
                    metadata = get_metadata_for_face(face_obj)
                    state = metadata.get("state", "Unknown")
                current_app.logger.info(
                    f"Retrieved state {state} for face {row['filename']}"
                )
                faces.append(
                    {
                        "id": row["id"],
                        "filename": row["filename"],
                        "year": row["yearbook_year"],
                        "decade": decade,
                        "state": state,
                        "similarity": random.randint(20, 40),
                    }
                )
        except Exception as e:
            current_app.logger.error(f"Fallback random fetch failed: {e}")
        finally:
            conn.close()
    return faces


def format_faces_for_display(
    faces, with_state=True, with_image_url=True, static_prefix="extracted_faces"
):
    """
    Given a list of face DB rows (tuples or dicts), return a list of dicts with id, state, and image_url for rendering.
    """
    from flask import url_for  # Import here to avoid circular imports

    formatted = []
    for row in faces:
        # Support both tuple and dict row types
        if isinstance(row, dict):
            face_id = row.get("id")
            filename = row.get("filename")
            state = row.get("state", "Unknown") if with_state else None
        else:
            face_id = row[0]
            filename = row[1]
            state = row[2] if with_state and len(row) > 2 and row[2] else "Unknown"
        face_dict = {"id": face_id}
        if with_state:
            face_dict["state"] = state
        if with_image_url and filename:
            face_dict["image_url"] = url_for(
                "static", filename=f"{static_prefix}/{filename}"
            )
        formatted.append(face_dict)
    return formatted


def format_matches_for_display(matches, user_id=None, static_prefix="extracted_faces"):
    """
    Format a list of match dicts for display in match templates, adding image_url and ensuring required fields.
    """
    from flask import url_for

    formatted = []
    for m in matches:
        filename = m.get("filename")
        match = dict(m)  # shallow copy
        if "image_url" not in match and filename:
            match["image_url"] = url_for(
                "static", filename=f"{static_prefix}/{filename}"
            )
        if user_id is not None:
            match["user_id"] = user_id
        formatted.append(match)
    return formatted

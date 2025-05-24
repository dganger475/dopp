from flask import current_app

from utils.db.database import get_db_connection
from utils.face.recognition import extract_face_encoding, find_similar_faces


def get_similar_faces(encoding, top_k=100):
    """Wrapper for similarity search."""
    return find_similar_faces(encoding, top_k=top_k)


# --- MOVED FROM face_matching.py ---
def query_faces_directly(image_path, top_k=10):
    """
    Try to extract a face encoding and run a similarity search. If encoding fails, return the top_k faces by popularity (match_count) as fallback.
    Adds a 'fallback' flag to each result if using fallback mode.
    """
    results = []
    fallback = False
    current_app.logger.info(f"Direct query for faces using image: {image_path}")
    try:
        encoding = extract_face_encoding(image_path)
        if encoding is not None and hasattr(encoding, "shape"):
            current_app.logger.info(
                f"Successfully extracted encoding with shape {encoding.shape}"
            )
            # Use real similarity search
            matches = find_similar_faces(encoding, top_k=top_k)
            if matches and len(matches) > 0:
                current_app.logger.info(
                    f"Found {len(matches)} similar faces using FAISS"
                )
                for match in matches:
                    match["fallback"] = False
                results = matches
                return results
            else:
                current_app.logger.info(
                    "No FAISS matches found; falling back to popular DB faces"
                )
                fallback = True
        else:
            current_app.logger.warning(
                "Face encoding extraction returned None or invalid encoding"
            )
            fallback = True
    except Exception as e:
        current_app.logger.error(f"Face encoding failed for {image_path}: {e}")
        fallback = True
    if fallback:
        # Fallback: return top_k faces with highest match_count plus some random faces for diversity
        current_app.logger.info("Using fallback database query for popular faces")
        conn = get_db_connection()
        try:
            # Get a mix of popular and diverse faces
            cursor = conn.cursor()
            # Get some popular faces (60% of results)
            popular_limit = int(top_k * 0.6)
            cursor.execute(
                """
                SELECT f.id, f.filename, f.school_name, f.yearbook_year, f.page_number, f.state, COUNT(um.id) as match_count
                FROM faces f
                LEFT JOIN user_matches um ON f.filename = um.match_filename
                GROUP BY f.filename
                ORDER BY match_count DESC
                LIMIT ?
            """,
                (popular_limit,),
            )
            popular_rows = cursor.fetchall()
            # Get some random faces from different states (40% of results)
            diverse_limit = top_k - len(popular_rows)
            cursor.execute(
                """
                SELECT f.id, f.filename, f.school_name, f.yearbook_year, f.page_number, f.state, COUNT(um.id) as match_count
                FROM faces f
                LEFT JOIN user_matches um ON f.filename = um.match_filename
                GROUP BY f.filename
                ORDER BY RANDOM()
                LIMIT ?
            """,
                (diverse_limit,),
            )
            diverse_rows = cursor.fetchall()
            # Combine the results
            all_rows = popular_rows + diverse_rows
            for row in all_rows:
                # Use the actual 'state' from the database if available, otherwise 'Unknown'
                actual_state = row["state"] if row["state"] else "Unknown"
                current_app.logger.debug(
                    f"Retrieved state '{actual_state}' for face {row['filename']}"
                )
                results.append(
                    {
                        "filename": row["filename"],
                        "similarity": 0.5,  # Default similarity for fallback matches
                        "state": actual_state,
                        "year": (
                            row["yearbook_year"] if row["yearbook_year"] else "Unknown"
                        ),
                        "page": row["page_number"] if row["page_number"] else 0,
                        "match_count": row["match_count"] if row["match_count"] else 0,
                        # TODO: Consider using url_for for consistency: url_for('static', filename=f'extracted_faces/{row["filename"]}')
                        "image_url": f"/static/extracted_faces/{row['filename']}",
                        "fallback": True,
                        "id": row["id"],
                    }
                )
        finally:
            if conn:
                conn.close()
    current_app.logger.info(f"Returning {len(results)} faces from direct query")
    return results

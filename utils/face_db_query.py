"""
This module provides direct database query functions for face matching.
It properly handles the uploaded_by column to filter out a user's own uploads.
"""

import logging

from flask import current_app

import numpy as np

from .database import get_db_connection
from .face_context_fix import extract_with_app_context, run_with_app_context


def query_similar_faces(user_id, limit=20, exclude_filenames=None):
    """
    Get similar faces from the database, properly excluding the user's own uploads.

    Args:
        user_id: The current user's ID to exclude their own uploads
        limit: Maximum number of faces to return
        exclude_filenames: List of filenames to exclude (e.g., already matched)

    Returns:
        List of face dictionaries with metadata
    """
    if exclude_filenames is None:
        exclude_filenames = []

    # Log what we're doing
    if "current_app" in globals():
        current_app.logger.info(
            f"Direct DB query for user {user_id}, excluding {len(exclude_filenames)} existing matches"
        )

    results = []
    conn = get_db_connection()
    try:
        # Build query conditions
        exclude_user_condition = ""
        exclude_filename_condition = ""

        # Don't show the user their own uploads
        if user_id:
            exclude_user_condition = (
                f"AND (uploaded_by IS NULL OR uploaded_by != {user_id})"
            )

        # Don't show already matched/excluded faces
        if exclude_filenames:
            placeholders = ", ".join(["?" for _ in exclude_filenames])
            exclude_filename_condition = f"AND filename NOT IN ({placeholders})"

        # Get popular faces (60% of results)
        popular_limit = int(limit * 0.6)
        cursor = conn.cursor()

        query = f"""
            SELECT f.id, f.filename, f.school_name, f.yearbook_year, f.page_number, 
                   COUNT(um.id) as match_count
            FROM faces f
            LEFT JOIN user_matches um ON f.filename = um.match_filename
            WHERE 1=1 {exclude_user_condition} {exclude_filename_condition}
            GROUP BY f.filename
            ORDER BY match_count DESC
            LIMIT ?
        """

        # Handle the excluded filenames in the query parameters
        query_params = []
        if exclude_filenames:
            query_params.extend(exclude_filenames)
        query_params.append(popular_limit)

        cursor.execute(query, query_params)
        popular_rows = cursor.fetchall()

        # Get diverse random faces (40% of results)
        diverse_limit = limit - len(popular_rows)
        if diverse_limit > 0:
            query = f"""
                SELECT f.id, f.filename, f.school_name, f.yearbook_year, f.page_number, 
                       COUNT(um.id) as match_count
                FROM faces f
                LEFT JOIN user_matches um ON f.filename = um.match_filename
                WHERE 1=1 {exclude_user_condition} {exclude_filename_condition}
                GROUP BY f.filename
                ORDER BY RANDOM()
                LIMIT ?
            """

            # Handle the excluded filenames in the query parameters
            query_params = []
            if exclude_filenames:
                query_params.extend(exclude_filenames)
            query_params.append(diverse_limit)

            cursor.execute(query, query_params)
            diverse_rows = cursor.fetchall()
        else:
            diverse_rows = []

        # Combine the results
        all_rows = popular_rows + diverse_rows

        # Format the results
        for row in all_rows:
            state = "Unknown"
            if row["school_name"] and row["school_name"].strip():
                state = row["school_name"]

            if "current_app" in globals():
                current_app.logger.info(
                    f"Retrieved state {state} for face {row['filename']}"
                )

            results.append(
                {
                    "filename": row["filename"],
                    "similarity": 0.5,  # Default similarity for database matches
                    "state": state,
                    "year": row["yearbook_year"] if row["yearbook_year"] else "Unknown",
                    "page": row["page_number"] if row["page_number"] else 0,
                    "match_count": row["match_count"] if row["match_count"] else 0,
                    "image_url": f"/static/extracted_faces/{row['filename']}",
                    "fallback": True,
                    "id": row["id"],
                }
            )
    except Exception as e:
        if "current_app" in globals():
            current_app.logger.error(f"Database query error: {e}")
    finally:
        if conn:
            conn.close()

    return results

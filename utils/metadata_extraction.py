"""Utility functions for extracting metadata from filenames and faces."""

import logging
import re
import sqlite3

from flask import current_app

from config.face_config import (
    DECADE_PATTERN,
    DEFAULT_DECADE,
    DEFAULT_STATE,
    STATE_NAMES_LOWERCASE,
    US_STATES,
    YEAR_PATTERN,
)
from utils.db.database import get_db_connection


def extract_state_from_school(school_name):
    """
    Extract state from a school name, typically in format "School Name, State"

    Args:
        school_name: The school name to extract from

    Returns:
        State string or None if not found
    """
    if not school_name:
        return None

    # Check if it's in the format "School Name, State"
    if "," in school_name:
        return school_name.split(",")[-1].strip()

    # Check for state abbreviation at the end of the string
    for abbrev in US_STATES.keys():
        pattern = r"\b" + abbrev + r"\b"
        if re.search(pattern, school_name):
            return abbrev

    return None


def extract_state_from_filename(filename):
    """
    Extract state from filename through pattern matching

    Args:
        filename: The face filename

    Returns:
        State string or None if not found
    """
    if not filename:
        return None

    filename_lower = filename.lower()

    # Check for state abbreviation in filename
    for abbrev, name in US_STATES.items():
        if abbrev in filename.upper():
            return name

    # Check for state name in filename
    for state in STATE_NAMES_LOWERCASE:
        if state in filename_lower:
            return state.title()

    return None


def get_decade_from_year(year_str):
    """
    Extract decade from a year string

    Args:
        year_str: Year as a string

    Returns:
        Decade string (e.g., "1950s") or "Unknown"
    """
    if not year_str:
        return "Unknown"

    try:
        year = int(year_str)
        # Get the first 3 digits of the year for 1000+ or just the first digit for years < 1000
        # then add the 0 to make it a proper decade
        return f"{str(year)[:3]}0s" if year >= 1000 else f"{str(year)[0]}0s"
    except (ValueError, TypeError):
        # Check if year might be embedded in the string (e.g., "Class of 1985")
        match = re.search(YEAR_PATTERN, str(year_str))
        if match:
            year = int(match.group(0))
            return f"{str(year)[:3]}0s" if year >= 1000 else f"{str(year)[0]}0s"
        return "Unknown"


def extract_decade_from_filename(filename):
    """
    Extract decade information directly from a filename

    Args:
        filename: The filename to extract from

    Returns:
        Decade string (e.g., "1980s") or None if not found
    """
    if not filename:
        return None

    # Try to extract decade from filename
    decade_match = re.search(DECADE_PATTERN, filename)
    if decade_match:
        # Ensure proper decade format
        decade = decade_match.group(1)
        # If it's already in proper format like "1980", just add "s"
        if len(decade) == 4 and decade.isdigit():
            return decade + "s"
        else:
            # Try to extract the year from it
            try:
                year = int(decade)
                return f"{str(year)[:3]}0s" if year >= 1000 else f"{str(year)[0]}0s"
            except ValueError:
                return decade + "s"

    # If no decade pattern, try to extract year and convert to decade
    year_match = re.search(YEAR_PATTERN, filename)
    if year_match:
        year = int(year_match.group(1))
        return f"{str(year)[:3]}0s" if year >= 1000 else f"{str(year)[0]}0s"

    return None


def get_metadata_for_face(face_obj):
    """
    Get comprehensive metadata for a face including state and decade

    Args:
        face_obj: Face object

    Returns:
        Dictionary with metadata including state and decade
    """
    metadata = {"decade": "Unknown", "state": "Unknown"}

    if not face_obj:
        return metadata

    # First check if the face object already has decade and state columns
    # from the updated database structure
    if hasattr(face_obj, "decade") and face_obj.decade:
        metadata["decade"] = face_obj.decade
    elif face_obj.yearbook_year:
        # Fall back to calculating from yearbook_year if decade column is empty
        metadata["decade"] = get_decade_from_year(face_obj.yearbook_year)

    if hasattr(face_obj, "state") and face_obj.state:
        metadata["state"] = face_obj.state
    else:
        # Try to get state from school name if state column is empty
        state = extract_state_from_school(face_obj.school_name)
        if state:
            metadata["state"] = state
            return metadata

        # If state not found in school name, try from filename
        state = extract_state_from_filename(face_obj.filename)
        if state:
            metadata["state"] = state
            return metadata

        # If we still don't have a state, check if there are other faces from the same school
        # that might have state information
        if face_obj.school_name:
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    cursor.execute(
                        """
                        SELECT school_name FROM faces 
                        WHERE school_name LIKE ? AND school_name LIKE '%,%'
                        LIMIT 1
                    """,
                        (f"%{face_obj.school_name}%",),
                    )

                    result = cursor.fetchone()
                    if result and "," in result["school_name"]:
                        state = extract_state_from_school(result["school_name"])
                        if state:
                            metadata["state"] = state

                except sqlite3.Error as e:
                    logging.error(f"Database error searching for state: {e}")
                finally:
                    conn.close()

    # If we still don't have metadata, try to extract from filename
    if metadata["decade"] == "Unknown":
        decade = extract_decade_from_filename(face_obj.filename)
        if decade:
            metadata["decade"] = decade

    if metadata["state"] == "Unknown":
        state = extract_state_from_filename(face_obj.filename)
        if state:
            metadata["state"] = state

    return metadata


def enhance_metadata_from_filename(metadata, filename):
    """
    Enhance metadata with information extracted from a filename when values are unknown

    Args:
        metadata: Existing metadata dictionary with decade and state
        filename: Filename to extract information from

    Returns:
        Enhanced metadata dictionary
    """
    enhanced = metadata.copy()

    # Apply fallback logic for decade if it's unknown
    if enhanced.get("decade") == "Unknown" and filename:
        decade = extract_decade_from_filename(filename)
        if decade:
            enhanced["decade"] = decade
        else:
            enhanced["decade"] = DEFAULT_DECADE

    # Apply fallback logic for state if it's unknown
    if enhanced.get("state") == "Unknown" and filename:
        state = extract_state_from_filename(filename)
        if state:
            enhanced["state"] = state
        else:
            enhanced["state"] = DEFAULT_STATE

    return enhanced

import logging
import re
import sqlite3

from flask import current_app

from utils.db.database import get_db_connection
from utils.metadata_extraction import get_decade_from_year


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

    # Common state abbreviations
    state_abbrevs = [
        "AL",
        "AK",
        "AZ",
        "AR",
        "CA",
        "CO",
        "CT",
        "DE",
        "FL",
        "GA",
        "HI",
        "ID",
        "IL",
        "IN",
        "IA",
        "KS",
        "KY",
        "LA",
        "ME",
        "MD",
        "MA",
        "MI",
        "MN",
        "MS",
        "MO",
        "MT",
        "NE",
        "NV",
        "NH",
        "NJ",
        "NM",
        "NY",
        "NC",
        "ND",
        "OH",
        "OK",
        "OR",
        "PA",
        "RI",
        "SC",
        "SD",
        "TN",
        "TX",
        "UT",
        "VT",
        "VA",
        "WA",
        "WV",
        "WI",
        "WY",
    ]

    # Check for state abbreviation at the end of the string
    for abbrev in state_abbrevs:
        pattern = r"\b" + abbrev + r"\b"
        if re.search(pattern, school_name):
            return abbrev

    return None


def extract_state_from_filename(filename):
    """
    Extract state from filename through pattern matching or database lookup

    Args:
        filename: The face filename

    Returns:
        State string or None if not found
    """
    if not filename:
        return None

    # Common state names in lowercase for pattern matching
    state_names = [
        "alabama",
        "alaska",
        "arizona",
        "arkansas",
        "california",
        "colorado",
        "connecticut",
        "delaware",
        "florida",
        "georgia",
        "hawaii",
        "idaho",
        "illinois",
        "indiana",
        "iowa",
        "kansas",
        "kentucky",
        "louisiana",
        "maine",
        "maryland",
        "massachusetts",
        "michigan",
        "minnesota",
        "mississippi",
        "missouri",
        "montana",
        "nebraska",
        "nevada",
        "new hampshire",
        "new jersey",
        "new mexico",
        "new york",
        "north carolina",
        "north dakota",
        "ohio",
        "oklahoma",
        "oregon",
        "pennsylvania",
        "rhode island",
        "south carolina",
        "south dakota",
        "tennessee",
        "texas",
        "utah",
        "vermont",
        "virginia",
        "washington",
        "west virginia",
        "wisconsin",
        "wyoming",
    ]

    filename_lower = filename.lower()

    # Check for state name in filename
    for state in state_names:
        if state in filename_lower:
            return state.title()

    return None


def get_metadata_for_face(face):
    """Get metadata for a face."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT yearbook_year, school_name, page_number, decade, state
                FROM faces
                WHERE id = ?
                """,
                (face.id,)
            )
            row = cursor.fetchone()
            if row:
                return {
                    'yearbook_year': row[0],
                    'school_name': row[1],
                    'page_number': row[2],
                    'decade': row[3],
                    'state': row[4]
                }
            return {}
    except Exception as e:
        logging.error(f"Error getting metadata for face: {e}")
        return {}


def enhance_face_with_metadata(face_dict):
    """
    Enhance a face dictionary with metadata (state and decade)

    Args:
        face_dict: Dictionary representation of a face

    Returns:
        Enhanced dictionary with state and decade
    """
    # Initialize if not present
    if "decade" not in face_dict or not face_dict["decade"]:
        face_dict["decade"] = "Unknown"
    if "state" not in face_dict or not face_dict["state"]:
        face_dict["state"] = "Unknown"

    # Attempt to derive decade if unknown and yearbook_year is available
    if face_dict["decade"] == "Unknown" and face_dict.get("yearbook_year"):
        calculated_decade = get_decade_from_year(str(face_dict["yearbook_year"]))
        if calculated_decade:
            face_dict["decade"] = calculated_decade

    # Attempt to derive state if unknown
    if face_dict["state"] == "Unknown":
        if face_dict.get("school_name"):
            state = extract_state_from_school(face_dict["school_name"])
            if state:
                face_dict["state"] = state

        if face_dict["state"] == "Unknown" and face_dict.get(
            "filename"
        ):  # If still unknown, try filename
            state_from_filename = extract_state_from_filename(face_dict["filename"])
            if state_from_filename:
                face_dict["state"] = state_from_filename

    return face_dict

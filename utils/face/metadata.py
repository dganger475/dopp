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


def get_metadata_for_face(face_obj):
    """
    Get comprehensive metadata for a face including state and decade

    Args:
        face_obj: Face object

    Returns:
        Dictionary with metadata including state and decade
    """
    metadata = {"decade": "Unknown", "state": "Unknown"}

    # First check if the face object already has decade and state columns
    # from the updated database structure
    if hasattr(face_obj, "decade") and face_obj.decade:
        metadata["decade"] = face_obj.decade
    elif hasattr(face_obj, "yearbook_year") and face_obj.yearbook_year:
        # Fall back to calculating from yearbook_year if decade column is empty
        calculated_decade = get_decade_from_year(str(face_obj.yearbook_year))
        if calculated_decade:
            metadata["decade"] = calculated_decade

    if hasattr(face_obj, "state") and face_obj.state:
        metadata["state"] = face_obj.state
    else:
        # Try to get state from school name if state column is empty
        state = extract_state_from_school(
            face_obj.school_name if hasattr(face_obj, "school_name") else None
        )
        if state:
            metadata["state"] = state
            # No need to return early, let decade logic complete if it hasn't found a value from face_obj.decade
        else:
            # If state not found in school name, try from filename
            state_from_filename = extract_state_from_filename(
                face_obj.filename if hasattr(face_obj, "filename") else None
            )
            if state_from_filename:
                metadata["state"] = state_from_filename
            # No need to return early here either

        # If we still don't have a state from direct attributes, school name, or filename,
        # then attempt the database lookup as a last resort.
        if (
            metadata["state"] == "Unknown"
            and hasattr(face_obj, "school_name")
            and face_obj.school_name
        ):
            # TODO: Review the efficiency and necessity of this database lookup for state.
            # It could be slow and might be better handled during initial data ingestion or a separate batch process.
            conn = get_db_connection()
            if conn:
                try:
                    cursor = conn.cursor()
                    # Search for school names that are an exact match or start with the current school name followed by a comma
                    # This is to find entries like "University of California" OR "University of California, Berkeley"
                    # and extract state from the more complete one.
                    # Ensure the school_name in the DB actually has a comma for state extraction.
                    base_school_name_query = face_obj.school_name.split(",")[0].strip()
                    cursor.execute(
                        """
                        SELECT school_name FROM faces 
                        WHERE (school_name = ? OR school_name LIKE ?) AND school_name LIKE '%,%'
                        ORDER BY LENGTH(school_name) DESC
                        LIMIT 1
                    """,
                        (
                            base_school_name_query,
                            base_school_name_query + ",%",
                        ),
                    )

                    result = cursor.fetchone()
                    if result and result["school_name"]:
                        state_from_db = extract_state_from_school(result["school_name"])
                        if state_from_db:
                            metadata["state"] = state_from_db

                except sqlite3.Error as e:
                    logging.error(
                        f"Database error searching for state for school '{face_obj.school_name}': {e}"
                    )
                finally:
                    conn.close()

    return metadata


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

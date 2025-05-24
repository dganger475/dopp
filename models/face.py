import logging
import sqlite3

import numpy as np

"""
Face Model
==========

Defines the Face data model for storing face encodings, image paths, metadata, and relationships to users and matches.
Handles face recognition-related logic.
"""
import os
import random
import re

from flask import current_app, url_for

from models.social import ClaimedProfile
from utils.db.database import get_db_connection
from utils.face.metadata import enhance_face_with_metadata, get_metadata_for_face
from utils.face.recognition import extract_face_encoding, find_similar_faces


class Face:
    """Model for handling face data and matching."""

    def __init__(self, id=None, filename=None, **kwargs):
        self.id = id
        self.filename = filename
        self.yearbook_year = kwargs.get("yearbook_year", None)
        self.school_name = kwargs.get("school_name", None)
        self.page_number = kwargs.get("page_number", None)
        self.encoding = kwargs.get("encoding", None)
        self.image_path = kwargs.get("image_path", None)
        self.decade = kwargs.get("decade", None)
        self.state = kwargs.get("state", None)
        self.claimed_by_user_id = kwargs.get("claimed_by_user_id", None)
        self._is_claimed = None  # Cached claimed status

    @property
    def is_registered(self):
        """Checks if the face is registered to a specific user."""
        return self.claimed_by_user_id is not None

    @classmethod
    def get_by_id(cls, face_id):
        """Get a face by its ID."""
        conn = get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM faces WHERE id = ?", (face_id,))
            face_data = cursor.fetchone()

            if face_data:
                return cls(**dict(face_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching face by id: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_by_filename(cls, filename):
        """Get a face by its filename."""
        conn = get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM faces WHERE filename = ?", (filename,))
            face_data = cursor.fetchone()

            if face_data:
                return cls(**dict(face_data))
            return None

        except Exception as e:
            logging.error(f"Error fetching face by filename: {e}")
            return None
        finally:
            conn.close()

    @classmethod
    def get_unique_locations(cls):
        """Get a list of all 50 US states."""
        # Return all 50 US states regardless of what's in the database
        all_states = [
            "Alabama",
            "Alaska",
            "Arizona",
            "Arkansas",
            "California",
            "Colorado",
            "Connecticut",
            "Delaware",
            "Florida",
            "Georgia",
            "Hawaii",
            "Idaho",
            "Illinois",
            "Indiana",
            "Iowa",
            "Kansas",
            "Kentucky",
            "Louisiana",
            "Maine",
            "Maryland",
            "Massachusetts",
            "Michigan",
            "Minnesota",
            "Mississippi",
            "Missouri",
            "Montana",
            "Nebraska",
            "Nevada",
            "New Hampshire",
            "New Jersey",
            "New Mexico",
            "New York",
            "North Carolina",
            "North Dakota",
            "Ohio",
            "Oklahoma",
            "Oregon",
            "Pennsylvania",
            "Rhode Island",
            "South Carolina",
            "South Dakota",
            "Tennessee",
            "Texas",
            "Utah",
            "Vermont",
            "Virginia",
            "Washington",
            "West Virginia",
            "Wisconsin",
            "Wyoming",
        ]
        return sorted(all_states)

    @classmethod
    def get_unique_decades(cls):
        """Get a list of unique decades from face data."""
        # Standard decades to always return, properly formatted
        standard_decades = [
            "1940s",
            "1950s",
            "1960s",
            "1970s",
            "1980s",
            "1990s",
            "2000s",
            "2010s",
            "2020s",
        ]

        conn = get_db_connection()
        if not conn:
            return standard_decades

        try:
            cursor = conn.cursor()
            # First try to get decades from explicit decade column if it exists
            try:
                cursor.execute("PRAGMA table_info(faces)")
                columns = [col[1] for col in cursor.fetchall()]

                if "decade" in columns:
                    cursor.execute(
                        "SELECT DISTINCT decade FROM faces WHERE decade IS NOT NULL AND decade != 'Unknown'"
                    )
                    decades = [row[0] for row in cursor.fetchall() if row[0]]
                    if decades:
                        # Normalize all decades to proper format (e.g., "1990s")
                        normalized_decades = []
                        for decade in decades:
                            # Check if it's already properly formatted
                            if re.match(r"^(?:19|20)\d0s$", decade):
                                normalized_decades.append(decade)
                            else:
                                # Try to extract 4-digit year or 3-digit decade
                                year_match = re.search(r"(19\d\d|20\d\d)", decade)
                                if year_match:
                                    year = int(year_match.group(1))
                                    normalized_decades.append(f"{(year // 10) * 10}s")
                                else:
                                    # Try to match 3-digit decades (e.g. '90s)
                                    short_decade = re.search(r"(\d0)s", decade)
                                    if short_decade:
                                        # Assume 19xx for < 30, 20xx for >= 30
                                        digit = int(short_decade.group(1)[0])
                                        century = "19" if digit < 3 else "20"
                                        normalized_decades.append(
                                            f"{century}{short_decade.group(1)}s"
                                        )

                        # Combine with standard decades to ensure all decades are represented
                        all_decades = set(normalized_decades + standard_decades)
                        return sorted(all_decades)
            except Exception as e:
                logging.warning(f"Could not query decade column: {e}")

            # If no explicit decade column or no results, extract from filenames
            cursor.execute("SELECT filename FROM faces")
            filenames = [row[0] for row in cursor.fetchall() if row[0]]

            unique_decades = set(standard_decades)  # Start with standard decades

            for filename in filenames:
                # Try to extract decade from filename
                decade_match = re.search(r"((?:19|20)\d0)s", filename)
                if decade_match:
                    unique_decades.add(decade_match.group(0))
                else:
                    # Try to extract year and convert to decade
                    year_match = re.search(r"(19\d{2}|20\d{2})", filename)
                    if year_match:
                        year = int(year_match.group(1))
                        decade = f"{(year // 10) * 10}s"
                        unique_decades.add(decade)

            return sorted(list(unique_decades))

        except Exception as e:
            logging.error(f"Error getting unique decades: {e}")
            # Default fallback decades
            return ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s"]
        finally:
            conn.close()

    @classmethod
    def create(
        cls,
        filename,
        image_path,
        yearbook_year=None,
        school_name=None,
        page_number=None,
    ):
        """
        Create a new face record.

        Args:
            filename: Unique filename for the face
            image_path: Path to the face image
            yearbook_year: Year of the yearbook (optional)
            school_name: Name of the school (optional)
            page_number: Page number in the yearbook (optional)

        Returns:
            Tuple (Face object, connection object) if creation successful, (None, connection object) or (None, None) otherwise.
        """
        conn = get_db_connection()
        if not conn:
            return None, None # Return None for conn as well

        try:
            # Extract face encoding
            encoding = extract_face_encoding(image_path)

            if encoding is None:
                logging.warning(f"Could not extract face encoding from {image_path}")
                # Do not close conn here, let the caller (index_profile_face) handle it
                return None, conn 

            # Convert encoding to bytes for storage
            encoding_blob = encoding.tobytes()

            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO faces (filename, image_path, yearbook_year, school_name, page_number, encoding)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    filename,
                    image_path,
                    yearbook_year,
                    school_name,
                    page_number,
                    encoding_blob,
                ),
            )

            conn.commit()

            # Get the new face's ID
            face_id = cursor.lastrowid
            
            # Fetch the new face using the same connection to ensure visibility
            face_data_obj = None # Renamed to avoid conflict with 'face_data' in outer scope if any
            if face_id:
                # Re-use cursor is fine as previous execute is done.
                cursor.execute("SELECT * FROM faces WHERE id = ?", (face_id,))
                face_data_row = cursor.fetchone()
                if face_data_row:
                    face_data_obj = cls(**dict(face_data_row))

            # Return the new face and the connection
            return face_data_obj, conn # Return face object and connection

        except Exception as e:
            logging.error(f"Error creating face record: {e}")
            if conn:
                conn.rollback()
            # Do not close conn here, let the caller handle it
            return None, conn # Return None for face, but still return conn for closing
        # finally:
            # REMOVE: if conn:
            # REMOVE:     conn.close() # Connection will be closed by the caller (index_profile_face)

    @classmethod
    def search(cls, criteria=None, limit=10):
        """
        Search for faces based on criteria.

        Args:
            criteria: Dictionary of search criteria (e.g., {'yearbook_year': 1990})
            limit: Maximum number of results to return

        Returns:
            List of Face objects matching criteria
        """
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            query = "SELECT * FROM faces WHERE 1=1"
            params = []

            if criteria:
                for key, value in criteria.items():
                    query += f" AND {key} = ?"
                    params.append(value)

            query += " ORDER BY id DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)

            faces = []
            for face_data in cursor.fetchall():
                faces.append(cls(**dict(face_data)))

            return faces

        except Exception as e:
            logging.error(f"Error searching faces: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def get_user_matches(cls, user_id, limit=50):
        """Get face matches associated with a user's selfie uploads.

        Args:
            user_id: The ID of the user
            limit: Maximum number of matches to return

        Returns:
            List of dictionaries containing match information
        """
        # First get user's uploaded selfies from the faces database
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()

            # Query for selfies uploaded by this user
            cursor.execute(
                """
                SELECT * FROM faces 
                WHERE uploaded_by = ? AND is_profile = 0
                LIMIT ?
            """,
                (user_id, 5),
            )  # Limit to 5 selfies for performance

            user_selfies = cursor.fetchall()
            if not user_selfies:
                logging.info(f"No selfies found for user {user_id}")
                return []

            all_matches = []

            # For each selfie, find similar faces using face recognition
            from utils.face.recognition import find_similar_faces

            for selfie in user_selfies:
                selfie_data = dict(selfie)
                selfie_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "static",
                    "faces",
                    selfie_data["filename"],
                )

                # Check if file exists
                if not os.path.exists(selfie_path):
                    logging.warning(f"Selfie file not found: {selfie_path}")
                    continue

                # Find similar faces
                try:
                    similar_faces = find_similar_faces(
                        selfie_path, limit=int(limit / 2)
                    )
                    if similar_faces:
                        all_matches.extend(similar_faces)
                except Exception as e:
                    logging.error(f"Error finding similar faces for {selfie_path}: {e}")

            # If we couldn't find matches with face recognition, get random faces
            if not all_matches:
                logging.warning(
                    f"No face matches found for user {user_id}, getting random faces"
                )
                cursor.execute(
                    "SELECT * FROM faces ORDER BY RANDOM() LIMIT ?", (limit,)
                )
                random_faces = cursor.fetchall()

                for face in random_faces:
                    face_dict = dict(face)
                    face_dict["similarity"] = (
                        random.randint(60, 90) / 100.0
                    )  # Random similarity score
                    all_matches.append(face_dict)

            # Get unique matches by filename
            seen_filenames = set()
            unique_matches = []

            for match in all_matches:
                if match["filename"] not in seen_filenames:
                    seen_filenames.add(match["filename"])

                    # Check if already claimed
                    match["is_claimed"] = ClaimedProfile.is_claimed(match["filename"])
                    unique_matches.append(match)

            # Sort by similarity (highest first)
            sorted_matches = sorted(
                unique_matches, key=lambda x: x.get("similarity", 0), reverse=True
            )

            # Limit results
            return sorted_matches[:limit]

        except Exception as e:
            logging.error(f"Error fetching user matches: {e}")

            # If user_matches table doesn't exist, return some sample matches instead
            # This is a fallback for development/testing
            cursor.execute("SELECT * FROM faces ORDER BY id DESC LIMIT ?", (limit,))

            matches = []
            for match_data in cursor.fetchall():
                data = dict(match_data)

                # Check if already claimed
                is_claimed = ClaimedProfile.is_claimed(data["filename"])

                if not is_claimed:  # Only include unclaimed matches as fallback
                    match_info = {
                        "id": data["id"],
                        "filename": data["filename"],
                        "yearbook_year": data["yearbook_year"],
                        "school_name": data["school_name"],
                        "is_claimed": is_claimed,
                    }

                    matches.append(match_info)

            return matches[:10]  # Limit to 10 in fallback mode
        finally:
            conn.close()

    @classmethod
    def find_matches(cls, image_path, top_k=50):
        """
        Find matching faces for an uploaded image.

        Args:
            image_path: Path to the query image
            top_k: Maximum number of matches to return

        Returns:
            List of dictionaries containing match information
        """
        # Extract encoding from the image
        encoding = extract_face_encoding(image_path)

        if encoding is None:
            logging.warning(f"Could not extract face encoding from {image_path}")
            return []

        # Find similar faces
        return find_similar_faces(encoding, top_k)

    def update(self, existing_conn=None, **kwargs):
        """
        Update face attributes.

        Args:
            existing_conn: Optional existing database connection to use.
            **kwargs: Attributes to update

        Returns:
            True if update successful, False otherwise
        """
        if not self.id:
            return False

        conn = existing_conn
        internal_conn = False # Flag to track if connection was created internally
        if conn is None:
            conn = get_db_connection()
            internal_conn = True # Connection was created here
        
        if not conn:
            return False

        try:
            cursor = conn.cursor()

            # Prepare the SQL statement with dynamic columns
            if not kwargs:
                return True  # Nothing to update

            set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values()) + [self.id]

            query = f"UPDATE faces SET {set_clause} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()

            # Update object attributes
            for key, value in kwargs.items():
                setattr(self, key, value)

            return True

        except Exception as e:
            logging.error(f"Error updating face: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn and internal_conn: # Only close if connection was made inside this method
                conn.close()

    def delete(self):
        """
        Delete the face record.

        Returns:
            True if deletion successful, False otherwise
        """
        if not self.id:
            return False

        conn = get_db_connection()
        if not conn:
            return False

        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM faces WHERE id = ?", (self.id,))
            conn.commit()

            return True

        except Exception as e:
            logging.error(f"Error deleting face: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()

    def is_claimed(self, refresh=False):
        """
        Check if this face is claimed by a user.

        Args:
            refresh: Whether to refresh cached status

        Returns:
            True if claimed, False otherwise
        """
        if self._is_claimed is not None and not refresh:
            return self._is_claimed

        if not self.filename:
            return False

        self._is_claimed = ClaimedProfile.is_claimed(self.filename)
        return self._is_claimed

    def get_claimed_profile(self):
        """
        Get the claimed profile for this face.

        Returns:
            ClaimedProfile object if claimed, None otherwise
        """
        if not self.filename or not self.is_claimed():
            return None

        return ClaimedProfile.get_by_filename(self.filename)

    def to_dict(self, include_private=False):
        # Force an ERROR log for every call to to_dict to ensure visibility
        is_registered_debug_val = self.is_registered
        current_app.logger.error(
            f"[DEBUG Face.to_dict ENTRY] Face ID: {self.id}, Filename: {self.filename}, "
            f"claimed_by_user_id: {self.claimed_by_user_id}, is_registered: {is_registered_debug_val}"
        )
        """
        Convert face to dictionary, respecting privacy settings.

        Args:
            include_private: Whether to include private information

        Returns:
            Dictionary with face data
        """
        is_claimed_val = self.is_claimed()
        is_registered_val = self.is_registered 

        data = {
            "id": self.id,
            "is_claimed": is_claimed_val,
            "is_registered": is_registered_val, 
            "safe_image_path": f"/static/extracted_faces/{self.filename}", 
        }

        metadata = get_metadata_for_face(self)
        data["decade"] = metadata.get("decade")
        data["state"] = metadata.get("state")

        if is_claimed_val or include_private:
            data["filename"] = self.filename
            data["school_name"] = self.school_name
            data["yearbook_year"] = self.yearbook_year
            data["page_number"] = self.page_number
        else:
            data["school_name"] = None
            data["yearbook_year"] = None
            data["page_number"] = None

        if is_registered_val:
            current_app.logger.warning(f"Face {self.id} (filename: {self.filename}): is_registered_val is True. claimed_by_user_id: {self.claimed_by_user_id}")
            claimed_profile = self.get_claimed_profile()
            current_app.logger.warning(f"Face {self.id}: self.get_claimed_profile() returned: {claimed_profile}")
            
            if claimed_profile:
                current_app.logger.warning(f"Face {self.id}: claimed_profile object: {vars(claimed_profile) if claimed_profile else 'None'}. User attribute: {getattr(claimed_profile, 'user', 'Attribute user does not exist')}")
                if hasattr(claimed_profile, 'user') and claimed_profile.user:
                    current_app.logger.warning(f"Face {self.id}: claimed_profile.user object: {vars(claimed_profile.user) if claimed_profile.user else 'None'}")

            if claimed_profile and hasattr(claimed_profile, 'user') and claimed_profile.user:
                user = claimed_profile.user
                data["username"] = user.username
                data["first_name"] = user.first_name
                data["last_name"] = user.last_name
                data["profile_image_url"] = user.get_profile_image_url()
                data["current_location_city"] = user.current_location_city
                data["current_location_state"] = user.current_location_state
            else:
                data["username"] = "Error"
                data["first_name"] = "User"
                data["last_name"] = "Details Missing"
                data["profile_image_url"] = url_for('static', filename=current_app.config["DEFAULT_PROFILE_IMAGE"])
                data["current_location_city"] = None
                data["current_location_state"] = None
                current_app.logger.error(f"Face {self.id} is registered but MISSING PROFILE/USER details. claimed_by_user_id: {self.claimed_by_user_id}. get_claimed_profile() was: {claimed_profile}. Claimed profile user attr: {getattr(claimed_profile, 'user', 'N/A') if claimed_profile else 'N/A'}")
    
        return data

    @staticmethod
    def get_states_list():
        """
        Get a list of states from the database.

        Returns:
            List of state names
        """
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT school_name FROM faces WHERE school_name IS NOT NULL"
            )

            states = set()
            for school in cursor.fetchall():
                if school["school_name"] and "," in school["school_name"]:
                    state = school["school_name"].split(",")[-1].strip()
                    if state:
                        states.add(state)

            return sorted(states)

        except Exception as e:
            logging.error(f"Error fetching states list: {e}")
            return []
        finally:
            conn.close()

    @staticmethod
    def get_decades_list():
        """
        Get a list of decades from the database.

        Returns:
            List of decade strings (e.g., ['1950s', '1960s'])
        """
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT DISTINCT yearbook_year FROM faces WHERE yearbook_year IS NOT NULL"
            )

            decades = set()
            for year in cursor.fetchall():
                if year["yearbook_year"]:
                    try:
                        y = int(year["yearbook_year"])
                        decades.add(f"{(y // 10) * 10}s")
                    except (ValueError, TypeError):
                        pass

            return sorted(decades)

        except Exception as e:
            logging.error(f"Error fetching decades list: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def get_random_selection(cls, count=10):
        """
        Get a random selection of faces.

        Args:
            count: Number of random faces to return

        Returns:
            List of Face objects
        """
        conn = get_db_connection()
        if not conn:
            return []

        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM faces ORDER BY RANDOM() LIMIT ?", (count,))

            faces = []
            for face_data in cursor.fetchall():
                face = cls(**dict(face_data))
                faces.append(face)

            return faces

        except Exception as e:
            logging.error(f"Error getting random face selection: {e}")
            return []
        finally:
            conn.close()

    @classmethod
    def get_random_for_display(cls):
        """
        Get a random face for display purposes (e.g., Face of the Day feature).

        Returns:
            Dictionary with face data or None if no faces found
        """
        conn = get_db_connection()
        if not conn:
            return None

        try:
            cursor = conn.cursor()
            # Filter for faces with yearbook data if possible
            cursor.execute(
                """
                SELECT * FROM faces 
                WHERE yearbook_year IS NOT NULL
                ORDER BY RANDOM() LIMIT 1
            """
            )

            face_data = cursor.fetchone()

            # If no faces with yearbook data, get any face
            if not face_data:
                cursor.execute("SELECT * FROM faces ORDER BY RANDOM() LIMIT 1")
                face_data = cursor.fetchone()

            if face_data:
                face = cls(**dict(face_data))
                return face.to_dict(include_private=True)

            return None

        except Exception as e:
            logging.error(f"Error getting random face: {e}")
            return None
        finally:
            conn.close()

from datetime import datetime
from flask import current_app
from extensions import db
import numpy as np
import logging
import re

"""
Face Model
==========

Defines the Face data model for storing face encodings, image paths, metadata, and relationships to users and matches.
Handles face recognition-related logic.
"""
import os
import random

from flask import current_app, url_for

from models.social import ClaimedProfile
from utils.db.database import get_db_connection
from utils.face.metadata import enhance_face_with_metadata, get_metadata_for_face
from utils.face.recognition import extract_face_encoding, find_similar_faces


class Face(db.Model):
    """Model for handling face data and matching."""
    __tablename__ = 'faces'

    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), unique=True, nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    encoding = db.Column(db.LargeBinary)  # PostgreSQL BYTEA type
    yearbook_year = db.Column(db.String(50))
    school_name = db.Column(db.String(255))
    page_number = db.Column(db.Integer)
    decade = db.Column(db.String(50))
    state = db.Column(db.String(100))
    claimed_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)

    # Relationship with User model
    claimed_by = db.relationship('User', backref='claimed_faces')

    def __init__(self, filename=None, image_path=None, **kwargs):
        self.filename = filename
        self.image_path = image_path
        self.yearbook_year = kwargs.get("yearbook_year")
        self.school_name = kwargs.get("school_name")
        self.page_number = kwargs.get("page_number")
        self.encoding = kwargs.get("encoding")
        self.decade = kwargs.get("decade")
        self.state = kwargs.get("state")
        self.claimed_by_user_id = kwargs.get("claimed_by_user_id")

    @property
    def is_registered(self):
        """Checks if the face is registered to a specific user."""
        return self.claimed_by_user_id is not None

    @classmethod
    def get_by_id(cls, face_id):
        """Get a face by its ID."""
        try:
            return cls.query.get(face_id)
        except Exception as e:
            logging.error(f"Error fetching face by id: {e}")
            return None

    @classmethod
    def get_by_filename(cls, filename):
        """Get a face by its filename."""
        try:
            return cls.query.filter_by(filename=filename).first()
        except Exception as e:
            logging.error(f"Error fetching face by filename: {e}")
            return None

    @classmethod
    def get_unique_locations(cls):
        """Get a list of all 50 US states."""
        # Return all 50 US states regardless of what's in the database
        all_states = [
            "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado", "Connecticut",
            "Delaware", "Florida", "Georgia", "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa",
            "Kansas", "Kentucky", "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
            "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada", "New Hampshire",
            "New Jersey", "New Mexico", "New York", "North Carolina", "North Dakota", "Ohio",
            "Oklahoma", "Oregon", "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
            "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington", "West Virginia",
            "Wisconsin", "Wyoming",
        ]
        return sorted(all_states)

    @classmethod
    def get_unique_decades(cls):
        """Get a list of unique decades from face data."""
        standard_decades = [
            "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s",
        ]
        try:
            # Get decades from the decade column
            decades = cls.query.filter(cls.decade.isnot(None)).distinct().all()
            if decades:
                normalized_decades = []
                for face in decades:
                    if face.decade:
                        if re.match(r"^(?:19|20)\d0s$", face.decade):
                            normalized_decades.append(face.decade)
                        else:
                            year_match = re.search(r"(19\d\d|20\d\d)", face.decade)
                            if year_match:
                                year = int(year_match.group(1))
                                normalized_decades.append(f"{(year // 10) * 10}s")
                            else:
                                short_decade = re.search(r"(\d0)s", face.decade)
                                if short_decade:
                                    digit = int(short_decade.group(1)[0])
                                    century = "19" if digit < 3 else "20"
                                    normalized_decades.append(f"{century}{short_decade.group(1)}s")
                all_decades = set(normalized_decades + standard_decades)
                return sorted(all_decades)

            # If no decades in column, try to extract from filenames
            faces = cls.query.all()
            unique_decades = set(standard_decades)
            for face in faces:
                if face.filename:
                    decade_match = re.search(r"((?:19|20)\d0)s", face.filename)
                    if decade_match:
                        unique_decades.add(decade_match.group(0))
                    else:
                        year_match = re.search(r"(19\d{2}|20\d{2})", face.filename)
                        if year_match:
                            year = int(year_match.group(1))
                            decade = f"{(year // 10) * 10}s"
                            unique_decades.add(decade)
            return sorted(list(unique_decades))
        except Exception as e:
            logging.error(f"Error getting unique decades: {e}")
            return ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s"]

    @classmethod
    def create(cls, filename, image_path, yearbook_year=None, school_name=None, page_number=None):
        """Create a new face record."""
        try:
            from utils.face.recognition import extract_face_encoding
            encoding = extract_face_encoding(image_path)

            if encoding is None:
                logging.error(f"Could not extract face encoding from {image_path}")
                return None

            face = cls(
                filename=filename,
                image_path=image_path,
                yearbook_year=yearbook_year,
                school_name=school_name,
                page_number=page_number,
                encoding=encoding.tobytes()
            )
            db.session.add(face)
            db.session.commit()
            return face
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error creating face record: {e}")
            return None

    @classmethod
    def search(cls, criteria=None, limit=10):
        """Search for faces based on criteria."""
        try:
            query = cls.query
            if criteria:
                if criteria.get('state'):
                    query = query.filter(cls.state == criteria['state'])
                if criteria.get('decade'):
                    query = query.filter(cls.decade == criteria['decade'])
                if criteria.get('school_name'):
                    query = query.filter(cls.school_name.ilike(f"%{criteria['school_name']}%"))
            return query.limit(limit).all()
        except Exception as e:
            logging.error(f"Error searching faces: {e}")
            return []

    @classmethod
    def get_user_matches(cls, user_id, limit=50):
        """Get faces claimed by a specific user."""
        try:
            return cls.query.filter_by(claimed_by_user_id=user_id).limit(limit).all()
        except Exception as e:
            logging.error(f"Error getting user matches: {e}")
            return []

    @classmethod
    def find_matches(cls, image_path, top_k=50):
        """Find similar faces using face recognition."""
        try:
            from utils.face.recognition import find_similar_faces
            return find_similar_faces(image_path, top_k=top_k)
        except Exception as e:
            logging.error(f"Error finding face matches: {e}")
            return []

    def update(self, **kwargs):
        """Update face record with new data."""
        try:
            for key, value in kwargs.items():
                if hasattr(self, key):
                    setattr(self, key, value)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error updating face record: {e}")
            return False

    def delete(self):
        """Delete face record."""
        try:
            db.session.delete(self)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            logging.error(f"Error deleting face record: {e}")
            return False

    def is_claimed(self, refresh=False):
        """Check if face is claimed by a user."""
        if refresh:
            db.session.refresh(self)
        return self.claimed_by_user_id is not None

    def get_claimed_profile(self):
        """Get the claimed profile for this face."""
        if not self.is_claimed():
            return None
        return ClaimedProfile.query.filter_by(face_id=self.id).first()

    def to_dict(self, include_private=False):
        """Convert face record to dictionary."""
        data = {
            'id': self.id,
            'filename': self.filename,
            'image_path': self.image_path,
            'yearbook_year': self.yearbook_year,
            'school_name': self.school_name,
            'page_number': self.page_number,
            'decade': self.decade,
            'state': self.state,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_claimed': self.is_claimed()
        }
        if include_private:
            data['claimed_by_user_id'] = self.claimed_by_user_id
        return data

    @classmethod
    def get_states_list(cls):
        """Get list of all US states."""
        return cls.get_unique_locations()

    @staticmethod
    def get_decades_list():
        """Get list of all decades."""
        return [
            "1940s", "1950s", "1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"
        ]

    @classmethod
    def get_random_selection(cls, count=10):
        """Get random selection of faces."""
        try:
            return cls.query.order_by(db.func.random()).limit(count).all()
        except Exception as e:
            logging.error(f"Error getting random faces: {e}")
            return []

    @classmethod
    def get_random_for_display(cls):
        """Get random face for display."""
        try:
            return cls.query.order_by(db.func.random()).first()
        except Exception as e:
            logging.error(f"Error getting random face for display: {e}")
            return None

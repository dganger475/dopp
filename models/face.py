"""Face model for DoppleGänger
===========================

This module defines the Face model and related database operations.
"""

import os
import logging
from datetime import datetime
from flask import current_app
from extensions import db
import numpy as np
import re

from flask import current_app, url_for

from models.social import ClaimedProfile
from utils.db.database import get_db_connection
from utils.face.metadata import enhance_face_with_metadata, get_metadata_for_face
from utils.face.recognition import extract_face_encoding, find_similar_faces

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Face(db.Model):
    """Face model for storing face encodings and metadata."""
    __tablename__ = 'faces'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    face_encoding = db.Column(db.LargeBinary, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('faces', lazy=True))

    def __init__(self, user_id, face_encoding):
        self.user_id = user_id
        self.face_encoding = face_encoding

    def to_dict(self):
        """Convert face object to dictionary."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def create(cls, user_id, face_encoding):
        """Create a new face record."""
        try:
            face = cls(user_id=user_id, face_encoding=face_encoding)
            db.session.add(face)
            db.session.commit()
            return face
        except Exception as e:
            logger.error(f"Error creating face record: {str(e)}")
            db.session.rollback()
            raise

    @classmethod
    def get_by_id(cls, face_id):
        """Get a face record by ID."""
        try:
            return cls.query.get(face_id)
        except Exception as e:
            logger.error(f"Error getting face by ID: {str(e)}")
            raise

    @classmethod
    def get_by_user_id(cls, user_id):
        """Get all face records for a user."""
        try:
            return cls.query.filter_by(user_id=user_id).all()
        except Exception as e:
            logger.error(f"Error getting faces by user ID: {str(e)}")
            raise

    def update(self, face_encoding=None):
        """Update a face record."""
        try:
            if face_encoding is not None:
                self.face_encoding = face_encoding
            self.updated_at = datetime.utcnow()
            db.session.commit()
            return self
        except Exception as e:
            logger.error(f"Error updating face record: {str(e)}")
            db.session.rollback()
            raise

    def delete(self):
        """Delete a face record."""
        try:
            db.session.delete(self)
            db.session.commit()
        except Exception as e:
            logger.error(f"Error deleting face record: {str(e)}")
            db.session.rollback()
            raise

    @property
    def is_registered(self):
        """Checks if the face is registered to a specific user."""
        return self.user_id is not None

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
            return cls.query.filter_by(user_id=user_id).limit(limit).all()
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

    def get_claimed_profile(self):
        """Get the claimed profile for this face."""
        if not self.is_registered:
            return None
        return ClaimedProfile.query.filter_by(face_id=self.id).first()

    def to_dict(self, include_private=False):
        """Convert face record to dictionary."""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_registered': self.is_registered
        }
        if include_private:
            data['face_encoding'] = self.face_encoding.hex()
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

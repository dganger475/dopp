import os
from pathlib import Path

import face_recognition

import numpy as np


class FaceMatcher:
    def __init__(self, database_path="static/extracted_faces/"):
        self.database_path = Path(database_path)
        self.known_faces = {}
        self._load_known_faces()

    def _load_known_faces(self):
        """Load and cache all known faces from the database"""
        for image_path in self.database_path.glob('*.jpg'):
            try:
                image = face_recognition.load_image_file(str(image_path))
                encodings = face_recognition.face_encodings(image)
                if encodings:
                    self.known_faces[image_path.name] = encodings[0]
            except Exception as e:
                print(f"Error loading {image_path}: {e}")

    def find_matches(self, selfie_path, tolerance=0.6):
        """Find matches for the uploaded selfie"""
        try:
            selfie_image = face_recognition.load_image_file(selfie_path)
            selfie_encoding = face_recognition.face_encodings(selfie_image)
            
            if not selfie_encoding:
                return []

            matches = []
            selfie_encoding = selfie_encoding[0]
            
            for filename, known_encoding in self.known_faces.items():
                distance = face_recognition.face_distance([known_encoding], selfie_encoding)[0]
                confidence = (1 - distance) * 100
                
                matches.append({
                    'filename': filename,
                    'confidence': confidence
                })
            
            return sorted(matches, key=lambda x: x['confidence'], reverse=True)

        except Exception as e:
            print(f"Error matching face: {e}")
            return []
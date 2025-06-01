import logging
import math
import os
import pickle

import face_recognition
import faiss
from flask import current_app
from PIL import Image

import numpy as np
from utils.db.database import get_db_connection

# Default paths if not using app config
DEFAULT_INDEX_PATH = "faces.index"
DEFAULT_MAP_PATH = "faces_filenames.pkl"


class FaceRecognizer:
    def __init__(self):
        # Initialize your face recognizer here
        pass

    # Add methods for face recognition as needed


# --- Functions moved from utils.similarity.calculator ---
def calculate_similarity(distance, threshold=0.6):
    """
    Calculate similarity percentage using the threshold-based formula:
    similarity_percent = max(0, 100 * (1 - (distance / threshold)))

    Args:
        distance (float): FAISS L2 distance
        threshold (float): Maximum distance threshold (default 0.6)
    Returns:
        float: Similarity percentage (0-100)
    """
    similarity = max(0, 100 * (1 - (distance / threshold)))
    return similarity


def format_similarity(similarity):
    """
    Format similarity percentage with 2 decimal places.

    Args:
        similarity (float): Similarity percentage

    Returns:
        str: Formatted similarity percentage string
    """
    return f"{similarity:.2f}%"


# --- End of moved functions ---


def rebuild_faiss_index(app=None):
    """Rebuild the FAISS index from face encodings in the database.
    Includes both faces from the faces table and users from the users table.

    Args:
        app: Optional Flask app instance for application context

    Returns:
        Boolean indicating success or failure
    """
    # Make sure we're using the faces.db file
    logging.info("Rebuilding FAISS index from faces.db file and users table")
    
    conn = get_db_connection(app=app)
    if not conn:
        logging.error("Failed to get database connection for faces.db")
        return False

    vectors = []
    filenames = []
    skipped_count = 0
    skipped_reasons = {}
    
    try:
        # 1. First get encodings from the faces table
        cursor = conn.cursor()
        cursor.execute(
            "SELECT filename, encoding FROM faces WHERE encoding IS NOT NULL"
        )
        face_rows = cursor.fetchall()
        logging.info(f"Found {len(face_rows)} potential face encodings in the faces table.")

        # Process face encodings
        for row in face_rows:
            filename = row[0]
            encoding_blob = row[1]
            try:
                encoding = np.frombuffer(encoding_blob, dtype=np.float64)
                if encoding.shape == (128,):
                    vectors.append(encoding)
                    filenames.append(filename)
                else:
                    skipped_count += 1
                    reason = f"Encoding shape is {encoding.shape}, expected (128,)"
                    skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
                    logging.warning(f"Skipping encoding for {filename}: {reason}")
            except Exception as e:
                skipped_count += 1
                reason = f"Error decoding face encoding: {e}"
                skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
                logging.warning(f"Skipping bad encoding for {filename}: {reason}")
        
        # 2. Now get encodings from the users table
        try:
            cursor.execute(
                "SELECT id, username, profile_image, face_encoding FROM users WHERE face_encoding IS NOT NULL"
            )
            user_rows = cursor.fetchall()
            logging.info(f"Found {len(user_rows)} potential user face encodings in the users table.")
            
            # Process user face encodings
            for row in user_rows:
                user_id = row[0]
                username = row[1]
                profile_image = row[2] or f"userprofile_{user_id}.jpg"
                encoding_blob = row[3]
                
                try:
                    encoding = np.frombuffer(encoding_blob, dtype=np.float64)
                    if encoding.shape == (128,):
                        vectors.append(encoding)
                        filenames.append(profile_image)  # Use profile image as filename
                        logging.debug(f"Added user encoding for {username} (ID: {user_id})")
                    else:
                        skipped_count += 1
                        reason = f"User encoding shape is {encoding.shape}, expected (128,)"
                        skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
                        logging.warning(f"Skipping user encoding for {username}: {reason}")
                except Exception as e:
                    skipped_count += 1
                    reason = f"Error decoding user encoding: {e}"
                    skipped_reasons[reason] = skipped_reasons.get(reason, 0) + 1
                    logging.warning(f"Skipping bad user encoding for {username}: {reason}")
        except Exception as e:
            logging.error(f"Error retrieving user encodings: {e}")
            # Continue with just face encodings if user encodings fail
        
        if not vectors:
            logging.info("No valid face encodings found in database.")
            return False

        if vectors:
            vectors_np = np.array(vectors, dtype=np.float32)
            index = faiss.IndexFlatL2(128)
            index.add(vectors_np)

            # Get paths with appropriate context handling
            if app:
                index_path = app.config.get("INDEX_PATH", DEFAULT_INDEX_PATH)
                map_path = app.config.get("MAP_PATH", DEFAULT_MAP_PATH)
            else:
                try:
                    index_path = current_app.config.get(
                        "INDEX_PATH", DEFAULT_INDEX_PATH
                    )
                    map_path = current_app.config.get("MAP_PATH", DEFAULT_MAP_PATH)
                except RuntimeError:
                    index_path = DEFAULT_INDEX_PATH
                    map_path = DEFAULT_MAP_PATH

            faiss.write_index(index, index_path)
            with open(map_path, "wb") as f:
                pickle.dump(filenames, f)

            logging.info(
                f"✅ FAISS index built with {len(filenames)} vectors. {skipped_count} encodings skipped."
            )
            for reason, count in skipped_reasons.items():
                logging.info(f"  Reason for skipping ({count}): {reason}")

            return True
        else:
            logging.info("No valid face encodings to build FAISS index.")
            return False

    except Exception as e:
        logging.error(f"Failed to rebuild FAISS index: {e}")
        return False
    finally:
        conn.close()


def find_similar_faces(encoding, top_k=50):
    """
    Find similar faces in the database using the FAISS index.

    Args:
        encoding: Face encoding vector
        top_k: Number of top matches to return

    Returns:
        List of dictionaries containing match information
    """
    return find_similar_faces_faiss(encoding, top_k)


def find_similar_faces_faiss(query_encoding, top_k=50):
    """
    Find similar faces using the FAISS index.

    Args:
        query_encoding: Face encoding to search for
        top_k: Number of top results to return

    Returns:
        List of dictionaries containing match information
    """
    try:
        # Get paths with appropriate context handling
        try:
            index_path = current_app.config.get("INDEX_PATH", DEFAULT_INDEX_PATH)
            map_path = current_app.config.get("MAP_PATH", DEFAULT_MAP_PATH)
        except RuntimeError:
            index_path = DEFAULT_INDEX_PATH
            map_path = DEFAULT_MAP_PATH

        # Check if index files exist
        if not os.path.exists(index_path) or not os.path.exists(map_path):
            logging.error(f"FAISS index files not found at {index_path} or {map_path}")
            return []

        # Load the FAISS index
        index = faiss.read_index(index_path)

        # Load the filename mapping
        with open(map_path, "rb") as f:
            filenames = pickle.load(f)

        # Convert the query to the right format
        query_vector = np.array([query_encoding], dtype=np.float32)

        # Perform the search
        k = min(top_k, len(filenames))  # Can't return more than we have
        distances, indices = index.search(query_vector, k)

        # Connect to database to get metadata
        conn = get_db_connection()
        cursor = conn.cursor()

        # Prepare results
        results = []
        # The threshold for similarity calculation is managed by calculate_similarity (defaults to 0.6)

        for i, idx in enumerate(indices[0]):
            if idx < 0 or idx >= len(filenames):
                continue  # Skip invalid indices

            filename = filenames[idx]
            distance = float(distances[0][i])

            # Get metadata from database - fetch 'state' explicitly
            cursor.execute(
                "SELECT school_name, yearbook_year, page_number, state FROM faces WHERE filename = ?",
                (filename,),
            )
            row = cursor.fetchone()

            school_name_val = "Unknown"
            year_val = "Unknown"
            page_val = 0
            state_val = "Unknown"

            if row:
                school_name_val = row[0] if row[0] else "Unknown"
                year_val = row[1] if row[1] else "Unknown"
                page_val = row[2] if row[2] else 0
                state_val = row[3] if row[3] else "Unknown"  # Correctly assign state

            # Calculate absolute similarity using the centralized function (now local)
            similarity_score = calculate_similarity(
                distance
            )  # Uses default threshold 0.6

            results.append(
                {
                    "filename": filename,
                    "distance": distance,
                    "similarity": round(similarity_score, 1),
                    "state": state_val,  # Use the correct state field
                    "school_name": school_name_val,  # Keep school_name as well if needed elsewhere
                    "year": year_val,
                    "page": page_val,
                }
            )

        # Sort by absolute similarity (still highest similarity first)
        results.sort(key=lambda x: x["similarity"], reverse=True)

        return results

    except FileNotFoundError:
        logging.error(
            f"FAISS index or map file not found. Index: {index_path}, Map: {map_path}"
        )
        return []
    except Exception as e:
        logging.error(f"Error finding similar faces: {e}")
        return []
    finally:
        if conn:
            conn.close()  # Ensure connection is closed


def get_real_image_path(image_path):
    # Convert a /static/... or static/... URL path to a real file path
    import os

    from flask import current_app

    if image_path.startswith("/static/"):
        return os.path.join(current_app.root_path, image_path[1:])
    elif image_path.startswith("static/"):
        return os.path.join(current_app.root_path, image_path)
    else:
        return image_path


def extract_face_encoding(image_path):
    """
    Extract face encoding from an image file with enhanced detection.
    Includes preprocessing and multiple detection methods to improve success rate.

    Args:
        image_path: Path to the image file

    Returns:
        Face encoding vector or None if no face is found
    """
    try:
        logging.info(f"Extracting face encoding for image: {image_path}")
        # Convert to real file path if needed
        real_path = get_real_image_path(image_path)
        logging.info(f"Loading and preprocessing image: {real_path}")

        # Try loading with PIL first to handle various formats
        try:
            with Image.open(real_path) as img:
                # Convert to RGB if not already
                img = img.convert("RGB")
                # Resize if image is too large (can help with detection)
                max_size = 1600
                if max(img.width, img.height) > max_size:
                    img.thumbnail((max_size, max_size))
                # Convert to numpy array
                image = np.array(img)
        except Exception as e:
            logging.warning(
                f"PIL loading failed, falling back to face_recognition: {e}"
            )
            image = face_recognition.load_image_file(real_path)

        # Try multiple detection methods with different parameters
        detection_methods = [
            ("hog", 1),  # Standard HOG
            ("hog", 2),  # HOG with upsample
            ("cnn", 1),  # CNN
            ("cnn", 2),  # CNN with upsample
        ]

        for model, upsample in detection_methods:
            try:
                logging.info(f"Attempting {model} detection with upsample={upsample}")
                face_locations = face_recognition.face_locations(
                    image, number_of_times_to_upsample=upsample, model=model
                )

                if face_locations:
                    logging.info(
                        f"Found {len(face_locations)} faces using {model} with upsample={upsample}"
                    )

                    # Try to get encodings with different parameters
                    for num_jitters in [1, 2, 3]:
                        try:
                            face_encodings = face_recognition.face_encodings(
                                image, face_locations, num_jitters=num_jitters
                            )

                            if face_encodings:
                                logging.info(
                                    f"Successfully extracted face encoding with num_jitters={num_jitters}"
                                )
                                return face_encodings[0]
                        except Exception as e:
                            logging.warning(
                                f"Encoding failed with num_jitters={num_jitters}: {e}"
                            )

                    break  # Move to next detection method if encoding failed
            except Exception as e:
                logging.warning(
                    f"Detection failed with {model} upsample={upsample}: {e}"
                )
                continue

        logging.warning(
            f"No successful face detection/encoding methods for {image_path}"
        )
        return None

    except Exception as e:
        logging.error(f"Error in face encoding extraction: {e}")
        return None

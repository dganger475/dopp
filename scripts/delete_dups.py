import logging
import sqlite3

import numpy as np

from app_config import DB_PATH

# Logging Configuration
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def get_db_connection():
    """Establish a connection to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logging.error(f"❌ Database connection failed: {e}")
        return None

def fetch_encodings():
    """Fetch all face encodings from the database."""
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, filename, image_path, encoding FROM faces")
        faces = cursor.fetchall()
        conn.close()
        return faces
    except Exception as e:
        logging.error(f"❌ Error fetching data: {e}")
        return []

def remove_duplicates():
    """Find and delete duplicate images based on face encodings."""
    faces = fetch_encodings()
    if not faces:
        logging.info("⚠️ No data found in database.")
        return

    seen_encodings = {}
    duplicates = []

    for entry in faces:
        face_id = entry["id"]
        filename = entry["filename"]
        image_path = entry["image_path"]
        encoding_blob = entry["encoding"]

        try:
            # Convert binary encoding to NumPy array
            encoding = np.frombuffer(encoding_blob, dtype=np.float64)

            # Convert encoding to a tuple (hashable) to check for duplicates
            encoding_tuple = tuple(encoding)

            if encoding_tuple in seen_encodings:
                # Found a duplicate
                duplicates.append((face_id, filename, image_path))
            else:
                # Store this encoding as seen
                seen_encodings[encoding_tuple] = (face_id, filename, image_path)

        except Exception as e:
            logging.error(f"❌ Error processing entry {filename}: {e}")

    if not duplicates:
        logging.info("✅ No duplicates found.")
        return

    # Delete duplicates from the database
    conn = get_db_connection()
    cursor = conn.cursor()

    for dup_id, dup_filename, dup_path in duplicates:
        try:
            cursor.execute("DELETE FROM faces WHERE id = ?", (dup_id,))
            logging.info(f"🗑️ Deleted duplicate: {dup_filename} ({dup_path})")
        except Exception as e:
            logging.error(f"❌ Error deleting {dup_filename}: {e}")

    conn.commit()
    conn.close()

    logging.info(f"✅ Successfully removed {len(duplicates)} duplicate entries.")

if __name__ == "__main__":
    remove_duplicates()

import logging
import os
import sqlite3

import face_recognition

# Database Path
DATABASE_FILE = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
EXTRACTED_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"

# Logging Setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def connect_db():
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        logging.info("✅ Database Connection Successful")
        return conn
    except sqlite3.Error as e:
        logging.error(f"❌ Database Connection Error: {e}", exc_info=True)
        return None

def rebuild_faces_table():
    """Rebuilds the faces table with the correct schema if the primary key is missing."""
    conn = connect_db()
    if not conn:
        return

    with conn:
        cursor = conn.cursor()

        # Check current columns
        cursor.execute("PRAGMA table_info(faces)")
        existing_columns = {row[1] for row in cursor.fetchall()}

        # Required columns for proper functionality
        required_columns = {"id", "filename", "image_path", "school", "year", "location", "extracted_date"}

        if "id" not in existing_columns:
            logging.warning("⚠️ Primary key column 'id' is missing. Rebuilding the table...")

            # Rename old table
            cursor.execute("ALTER TABLE faces RENAME TO faces_old")

            # Create a new table with the correct schema
            cursor.execute("""
                CREATE TABLE faces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filename TEXT UNIQUE,
                    image_path TEXT,
                    school TEXT,
                    year TEXT,
                    location TEXT,
                    extracted_date TEXT
                )
            """)

            # Copy data from old table to new table
            cursor.execute("""
                INSERT INTO faces (filename, image_path, school, year, location, extracted_date)
                SELECT filename, image_path, school, year, location, extracted_date FROM faces_old
            """)

            # Drop old table
            cursor.execute("DROP TABLE faces_old")

            conn.commit()
            logging.info("✅ Faces table successfully rebuilt with primary key.")

def clean_database():
    """Remove database entries for missing images."""
    conn = connect_db()
    if not conn:
        return

    with conn:
        cursor = conn.cursor()

        # Fetch all stored image paths
        cursor.execute("SELECT id, filename, image_path FROM faces")
        records = cursor.fetchall()

        deleted_count = 0
        for record in records:
            file_id, filename, image_path = record

            if not os.path.exists(image_path):
                logging.info(f"🗑️ Deleting database entry: {filename} (file not found)")
                cursor.execute("DELETE FROM faces WHERE id = ?", (file_id,))
                deleted_count += 1

        conn.commit()
        logging.info(f"✅ Cleaned database: Removed {deleted_count} missing file entries.")

def update_encodings():
    """Ensure all images in extracted_faces have encodings stored in the database."""
    conn = connect_db()
    if not conn:
        return

    with conn:
        cursor = conn.cursor()

        # Get all current filenames stored in the database
        cursor.execute("SELECT filename FROM faces")
        stored_filenames = {row[0] for row in cursor.fetchall()}

        new_encodings = 0
        for filename in os.listdir(EXTRACTED_FOLDER):
            if filename.lower().endswith((".jpg", ".jpeg", ".png")):
                file_path = os.path.join(EXTRACTED_FOLDER, filename)

                if filename not in stored_filenames:
                    # Process face encoding
                    image = face_recognition.load_image_file(file_path)
                    face_encodings = face_recognition.face_encodings(image)

                    if face_encodings:
                        encoding_blob = face_encodings[0].tobytes()

                        # Insert into the database
                        cursor.execute(
                            "INSERT INTO faces (filename, image_path, extracted_date) VALUES (?, ?, datetime('now'))",
                            (filename, file_path),
                        )
                        conn.commit()
                        new_encodings += 1
                        logging.info(f"✅ Added encoding for {filename}")

        logging.info(f"✅ Encoding update complete: {new_encodings} new encodings added.")

def sync_database():
    """Run the full sync process: Ensure schema, remove missing files & add encodings for new ones."""
    rebuild_faces_table()  # ✅ Fixes missing primary key issue
    clean_database()
    update_encodings()
    logging.info("✅ Database successfully synced with extracted_faces folder.")

# Run the sync
if __name__ == "__main__":
    sync_database()

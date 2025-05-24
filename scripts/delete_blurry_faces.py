import logging
import os
import sqlite3

import cv2

from app_config import DB_PATH

# Configuration
BLUR_THRESHOLD = 50  # Lower values mean blurrier (Try adjusting if needed)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def connect_db():
    """Connects to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        logging.info("✅ Database Connection Successful")
        return conn
    except sqlite3.Error as e:
        logging.error(f"⚠️ Database Connection Error: {e}", exc_info=True)
        return None

def is_blurry(image_path, threshold):
    """Checks if an image is blurry using the Laplacian variance method."""
    try:
        img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)  # Read as grayscale
        if img is None:
            logging.warning(f"⚠️ Could not read image: {image_path}")
            return True  # Treat as blurry if unreadable

        laplacian_var = cv2.Laplacian(img, cv2.CV_64F).var()  # Calculate variance
        return laplacian_var < threshold  # If variance is low, image is blurry
    except Exception as e:
        logging.error(f"⚠️ Error checking blur for {image_path}: {e}")
        return True  # Treat as blurry if error occurs

def cleanup_blurry_faces():
    """Identifies and removes blurry face images and database entries."""
    conn = connect_db()
    if not conn:
        return

    cursor = conn.cursor()

    try:
        # Fetch all filenames and image paths from the database
        cursor.execute("SELECT filename, image_path FROM faces")
        faces = cursor.fetchall()

        for filename, image_path in faces:
            full_image_path = os.path.join(os.getcwd(), image_path)  # Construct full image path

            if is_blurry(full_image_path, BLUR_THRESHOLD):
                logging.info(f"🗑️ Deleting blurry face: {filename}")

                # Delete the image file
                try:
                    os.remove(full_image_path)
                    logging.info(f"✅ Deleted image file: {full_image_path}")
                except OSError as e:
                    logging.error(f"⚠️ Error deleting image file {full_image_path}: {e}")

                # Delete the database entry (use filename to identify)
                cursor.execute("DELETE FROM faces WHERE filename=?", (filename,))
                logging.info(f"✅ Deleted database entry for {filename}")

                conn.commit()  # Commit after each deletion
            else:
                logging.info(f"✔️ Image {filename} is clear. Keeping it.")

    except sqlite3.Error as e:
        logging.error(f"⚠️ Database error during cleanup: {e}")
        conn.rollback()  # Rollback in case of error

    finally:
        if conn:
            conn.close()
            logging.info("✅ Database connection closed.")

if __name__ == "__main__":
    cleanup_blurry_faces()
    logging.info("✅ Blurry image cleanup process completed.")

import logging
import os
import sqlite3

from PIL import Image

from app_config import DB_PATH, EXTRACTED_FACES

# Minimum Image Size
MIN_WIDTH = 100
MIN_HEIGHT = 100

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


def find_small_images():
    """Find images smaller than 100x100 in the extracted_faces directory."""
    small_images = []

    for filename in os.listdir(EXTRACTED_FACES):
        file_path = os.path.join(EXTRACTED_FACES, filename)

        # Ensure it's an image file
        if filename.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
            try:
                with Image.open(file_path) as img:
                    width, height = img.size

                    if width < MIN_WIDTH or height < MIN_HEIGHT:
                        small_images.append(file_path)
            except Exception as e:
                logging.error(f"❌ Error processing image {filename}: {e}")

    return small_images


def delete_small_images_and_encodings():
    """Delete images smaller than 100x100 and remove their encodings from the database."""
    small_images = find_small_images()
    
    if not small_images:
        logging.info("✅ No small images found.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()

    for image_path in small_images:
        filename = os.path.basename(image_path)

        # Delete the image file
        try:
            os.remove(image_path)
            logging.info(f"🗑️ Deleted small image: {filename}")
        except Exception as e:
            logging.error(f"❌ Error deleting image {filename}: {e}")
            continue

        # Delete encoding from the database
        try:
            cursor.execute("DELETE FROM faces WHERE filename = ?", (filename,))
            logging.info(f"🗑️ Deleted encoding for: {filename}")
        except Exception as e:
            logging.error(f"❌ Error deleting encoding for {filename}: {e}")

    conn.commit()
    conn.close()
    
    logging.info(f"✅ Successfully removed {len(small_images)} small images and their encodings.")


if __name__ == "__main__":
    delete_small_images_and_encodings()

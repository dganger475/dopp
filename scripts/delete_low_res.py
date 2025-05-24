import logging
import os
import sqlite3

import cv2

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

IMAGE_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\static\sorted_faces"  # Root folder for images
DATABASE_FILE = r"C:\Users\1439\Documents\DopplegangerApp\faces.db" # Database path
RESOLUTION_THRESHOLD = (100, 100)  # Minimum resolution (width, height)

def connect_db():
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database connection error: {e}")
        return None

def delete_low_resolution_images():
    conn = connect_db()
    if conn is None:
        return

    cursor = conn.cursor()

    for root, _, files in os.walk(IMAGE_FOLDER):
        for filename in files:
            if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                full_image_path = os.path.join(root, filename)

                try:
                    img = cv2.imread(full_image_path)
                    if img is None:
                        logging.warning(f"Image not found: {full_image_path}")
                        continue

                    height, width, _ = img.shape
                    if width < RESOLUTION_THRESHOLD[0] or height < RESOLUTION_THRESHOLD[1]:
                        logging.info(f"Deleting low-resolution image: {full_image_path} (Resolution: {width}x{height})")

                        # Delete image file
                        os.remove(full_image_path)

                        # Delete from database
                        cursor.execute("DELETE FROM faces WHERE image_path = ?", (os.path.relpath(full_image_path, IMAGE_FOLDER),))
                        conn.commit()
                        logging.info(f"Database entry deleted for image path: {os.path.relpath(full_image_path, IMAGE_FOLDER)}")
                    else:
                        logging.info(f"Image {full_image_path} meets resolution requirements. (Resolution: {width}x{height})")

                except Exception as e:
                    logging.error(f"Error processing image {full_image_path}: {e}")

    if conn:
        conn.close()
    logging.info("Low-resolution image deletion process completed.")

if __name__ == "__main__":
    delete_low_resolution_images()
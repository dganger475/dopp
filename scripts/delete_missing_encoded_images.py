import os
import sqlite3

DATABASE_FILE = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
EXTRACTED_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"

def delete_missing_encoded_images():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Get all images with missing encodings
    cursor.execute("SELECT filename, image_path FROM faces WHERE encoding IS NULL OR encoding = ''")
    missing_images = cursor.fetchall()

    if not missing_images:
        print("✅ No images with missing encodings found. Nothing to delete.")
        conn.close()
        return

    print(f"🔹 Found {len(missing_images)} images to delete.\n")

    deleted_count = 0
    for filename, image_path in missing_images:
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
                print(f"✅ Deleted: {filename}")
                deleted_count += 1
            except Exception as e:
                print(f"⚠️ Failed to delete {filename}: {e}")

    conn.close()
    
    print(f"\n✅ Successfully deleted {deleted_count} images with missing encodings.")

delete_missing_encoded_images()

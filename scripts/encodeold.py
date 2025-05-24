import os
import shutil
import sqlite3
from concurrent.futures import ProcessPoolExecutor

import face_recognition
from tqdm import tqdm

import numpy as np

from app_config import DB_PATH, EXTRACTED_FACES

# --- CONFIG ---
BACKUP_PATH = "faces_backup_before_encoding.db"
NUM_WORKERS = 15
CHUNK_SIZE = 100

# --- FUNCTIONS ---

def backup_database():
    if os.path.exists(DB_PATH):
        shutil.copyfile(DB_PATH, BACKUP_PATH)
        print(f"✅ Backup created: {BACKUP_PATH}")
    else:
        print(f"❌ Database not found at {DB_PATH}")

def process_face(image_path):
    try:
        # Load the image and get face encodings
        image = face_recognition.load_image_file(image_path)
        encodings = face_recognition.face_encodings(image)
        
        if not encodings:
            return None, "No face found"
            
        return encodings[0], "success"
    except Exception as e:
        return None, str(e)

def encode_faces():
    # Create backup first
    backup_database()
    
    # Connect to database
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get all faces without encodings
    cursor.execute("SELECT filename FROM faces WHERE encoding IS NULL")
    faces_to_encode = cursor.fetchall()
    
    if not faces_to_encode:
        print("✅ No faces need encoding")
        return
        
    print(f"🔄 Processing {len(faces_to_encode)} faces...")
    
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = []
        for filename, in faces_to_encode:
            image_path = os.path.join(EXTRACTED_FACES, filename)
            if os.path.exists(image_path):
                futures.append((filename, executor.submit(process_face, image_path)))
        
        # Process results with progress bar
        for filename, future in tqdm(futures):
            encoding, status = future.result()
            if encoding is not None:
                cursor.execute(
                    "UPDATE faces SET encoding = ? WHERE filename = ?",
                    (encoding.tobytes(), filename)
                )
                conn.commit()
            else:
                print(f"❌ Failed to encode {filename}: {status}")
    
    conn.close()
    print("✅ Encoding complete")

if __name__ == "__main__":
    encode_faces()

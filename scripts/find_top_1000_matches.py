import json
import os
import sqlite3

import face_recognition

import numpy as np

# ----- CONFIG -----
TARGET_IMAGES = {
    "me": "input_faces/me.jpg",
    "wife": "input_faces/wife.jpg"
}
DB_PATH = "faces.db"
TOP_K = 1000
OUTPUT_DIR = "top_matches"
# ------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_encoding(image_path):
    image = face_recognition.load_image_file(image_path)
    encodings = face_recognition.face_encodings(image)
    if encodings:
        return encodings[0]
    else:
        raise ValueError(f"No face encoding found in {image_path}")

def fetch_db_encodings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT filename, encoding FROM faces WHERE encoding IS NOT NULL")
    data = cursor.fetchall()
    conn.close()

    encodings = []
    for filename, blob in data:
        arr = np.frombuffer(blob, dtype=np.float64)
        if arr.shape == (128,):
            encodings.append((filename, arr))
    return encodings

def compute_top_k_matches(target_encoding, all_faces, k):
    distances = []
    for filename, encoding in all_faces:
        dist = np.linalg.norm(target_encoding - encoding)
        distances.append((filename, float(dist)))
    distances.sort(key=lambda x: x[1])
    return distances[:k]

def main():
    print("🔍 Loading database face encodings...")
    all_faces = fetch_db_encodings()
    print(f"✅ Loaded {len(all_faces)} encodings from database.")

    for user_id, image_path in TARGET_IMAGES.items():
        print(f"\n👤 Processing matches for {user_id} from {image_path}")
        try:
            user_encoding = load_encoding(image_path)
        except ValueError as e:
            print(f"❌ {e}")
            continue

        top_matches = compute_top_k_matches(user_encoding, all_faces, TOP_K)

        output_path = os.path.join(OUTPUT_DIR, f"{user_id}_top{TOP_K}.json")
        with open(output_path, "w") as f:
            json.dump(top_matches, f, indent=2)
        print(f"💾 Saved top {TOP_K} matches for {user_id} to {output_path}")

if __name__ == "__main__":
    main()

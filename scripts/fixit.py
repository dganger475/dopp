# REBUILD_FAISS_AND_RECOVER_DB.PY (Parallel + Progress Bar)

import datetime
import multiprocessing
import os
import pickle
import shutil
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import face_recognition
import faiss
from tqdm import tqdm

import numpy as np

from app_config import DB_PATH, EXTRACTED_FACES, INDEX_PATH, MAP_PATH

# === CONFIG ===
BACKUP_DIR = Path("backups")
THREADS = multiprocessing.cpu_count()  # Use all available CPU cores

BACKUP_DIR.mkdir(exist_ok=True)

# === BACKUP ===
def backup():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if os.path.exists(DB_PATH):
        shutil.copy(DB_PATH, BACKUP_DIR / f"faces_backup_{timestamp}.db")
    if os.path.exists(INDEX_PATH):
        shutil.copy(INDEX_PATH, BACKUP_DIR / f"faces_backup_{timestamp}.index")
    if os.path.exists(MAP_PATH):
        shutil.copy(MAP_PATH, BACKUP_DIR / f"faces_backup_{timestamp}.pkl")

# === DATABASE INIT ===
def connect_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute('''CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        image_path TEXT,
        encoding BLOB,
        quality_flag TEXT
    )''')
    conn.commit()
    return conn

# === ENCODING CHECK ===
def is_valid_encoding(enc):
    return isinstance(enc, np.ndarray) and enc.shape == (128,) and np.isfinite(enc).all()

# === FACE PROCESSING ===
def process_face(img_path):
    filename = img_path.name
    try:
        img = face_recognition.load_image_file(str(img_path))
        encodings = face_recognition.face_encodings(img)
        if not encodings:
            return filename, None, "no_face"
        encoding = encodings[0]
        if not is_valid_encoding(encoding):
            return filename, None, "invalid"
        return filename, encoding, "good"
    except Exception as e:
        return filename, None, f"error: {e}"

# === MAIN ===
def rebuild():
    print("🔒 Backing up current DB and index...")
    backup()

    print("🔄 Rebuilding index from images in:", EXTRACTED_FACES)
    conn = connect_db()
    cursor = conn.cursor()

    face_files = sorted([f for f in EXTRACTED_FACES.glob("*.jpg")])
    existing_files = {row[0] for row in cursor.execute("SELECT filename FROM faces WHERE encoding IS NOT NULL").fetchall()}
    to_process = [f for f in face_files if f.name not in existing_files]

    index = faiss.IndexFlatL2(128)
    meta = []
    count_good = 0
    count_skipped = 0

    print(f"🧵 Using {THREADS} threads for parallel processing...")
    with ThreadPoolExecutor(max_workers=THREADS) as executor:
        futures = {executor.submit(process_face, img_path): img_path for img_path in to_process}
        for future in tqdm(as_completed(futures), total=len(futures), desc="Processing faces", ncols=100):
            filename, encoding, status = future.result()
            if encoding is not None and status == "good":
                try:
                    cursor.execute("INSERT OR REPLACE INTO faces (filename, image_path, encoding, quality_flag) VALUES (?, ?, ?, ?)",
                                   (filename, str(EXTRACTED_FACES / filename), encoding.tobytes(), status))
                    conn.commit()
                    index.add(np.array([encoding], dtype=np.float32))
                    meta.append({"filename": filename})
                    count_good += 1
                except Exception as e:
                    print(f"⚠️ DB error on {filename}: {e}")
                    count_skipped += 1
            else:
                count_skipped += 1

    print(f"✅ Finished: {count_good} good, {count_skipped} skipped, {len(face_files)} total")
    print("💾 Saving index...")
    faiss.write_index(index, str(INDEX_PATH))
    with open(MAP_PATH, "wb") as f:
        pickle.dump(meta, f)
    conn.close()

if __name__ == "__main__":
    rebuild()

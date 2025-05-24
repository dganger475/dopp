#!/usr/bin/env python3

import os
import pickle
import sqlite3
from concurrent.futures import ProcessPoolExecutor

import face_recognition
import faiss
from tqdm import tqdm

import numpy as np

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
DB_PATH           = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
FACES_DIR         = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"
INDEX_PATH        = r"C:\Users\1439\Documents\DopplegangerApp\faces.index"
MAP_PATH          = r"C:\Users\1439\Documents\DopplegangerApp\faces_filenames.pkl"

MAX_WORKERS       = os.cpu_count() or 1
ENCODE_CHUNK_SIZE = 200    # commit every 200 encodings
INDEX_CHUNK_SIZE  = 1000   # index 1 000 rows at a time
# ────────────────────────────────────────────────────────────────────────────────

def list_images(folder):
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith((".jpg", ".jpeg", ".png")):
                yield os.path.join(root, f)

def encode_one(path):
    img = face_recognition.load_image_file(path)
    encs = face_recognition.face_encodings(img)
    if not encs:
        return None
    vec = np.array(encs[0], dtype=np.float64)
    fn = os.path.relpath(path, FACES_DIR).replace("\\", "/")
    full = path.replace("\\", "/")
    return fn, full, vec.tobytes()

def upsert_batch(conn, batch):
    c = conn.cursor()
    for fn, full, blob in batch:
        c.execute(
            """
            INSERT INTO faces (filename, image_path, encoding)
            VALUES (?, ?, ?)
            ON CONFLICT(filename) DO UPDATE
              SET image_path = excluded.image_path,
                  encoding   = excluded.encoding
            """,
            (fn, full, sqlite3.Binary(blob))
        )
    conn.commit()

def main():
    # 1) prep DB
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
      CREATE TABLE IF NOT EXISTS faces (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        filename       TEXT,
        image_path     TEXT,
        encoding       BLOB,
        school         TEXT,
        year           TEXT,
        location       TEXT,
        extracted_date TEXT,
        yearbook_year  TEXT,
        school_name    TEXT,
        page_number    INTEGER,
        quality_score  REAL,
        quality_flag   TEXT
      )
    """)
    conn.commit()

    # 2) gather images
    paths = list(list_images(FACES_DIR))
    total = len(paths)
    if total == 0:
        print(f"No images found in {FACES_DIR}")
        return

    # 3) encode & upsert with map + tqdm
    buffer = []
    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as exe:
        for result in tqdm(exe.map(encode_one, paths),
                           total=total,
                           desc="🔄 Encode→Buffer",
                           unit="img"):
            if result:
                buffer.append(result)
            if len(buffer) >= ENCODE_CHUNK_SIZE:
                upsert_batch(conn, buffer)
                buffer.clear()

    # final flush
    if buffer:
        upsert_batch(conn, buffer)

    # 4) rebuild FAISS index in batches
    print("🔨 Rebuilding FAISS index…")
    idx = faiss.IndexFlatL2(128)
    filenames = []
    count = conn.execute("SELECT COUNT(*) FROM faces").fetchone()[0]

    for offset in range(0, count, INDEX_CHUNK_SIZE):
        rows = conn.execute(
            "SELECT filename, encoding FROM faces ORDER BY id LIMIT ? OFFSET ?",
            (INDEX_CHUNK_SIZE, offset)
        ).fetchall()
        mats = np.vstack([np.frombuffer(r[1], dtype=np.float64) for r in rows])
        idx.add(mats)
        filenames.extend(r[0] for r in rows)
        print(f"  • Indexed {min(offset+len(rows), count)}/{count}")

    faiss.write_index(idx, INDEX_PATH)
    with open(MAP_PATH, "wb") as f:
        pickle.dump(filenames, f)

    conn.close()
    print("✅ All done!\n"
          f"  • SQLite: {DB_PATH}\n"
          f"  • FAISS:  {INDEX_PATH}\n"
          f"  • Map:    {MAP_PATH}")

if __name__ == "__main__":
    main()

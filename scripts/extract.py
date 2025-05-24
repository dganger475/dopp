#!/usr/bin/env python3

import os
import pickle
import sqlite3

import face_recognition
import faiss
import fitz
from PIL import Image

import numpy as np

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
DB_PATH       = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
PDF_FOLDER    = r"C:\Users\1439\Documents\DopplegangerApp\downloads"
FACES_DIR     = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"
INDEX_PATH    = r"C:\Users\1439\Documents\DopplegangerApp\faces.index"
MAP_PATH      = r"C:\Users\1439\Documents\DopplegangerApp\faces_filenames.pkl"

# max dimension (width or height) for face detection pass
DETECT_MAX_DIM = 800  

# padding & final crop size
PADDING_RATIO = 0.25
TARGET_SIZE   = (256,256)
# ────────────────────────────────────────────────────────────────────────────────

def get_pdfs(folder):
    return sorted([
        os.path.join(folder, f)
        for f in os.listdir(folder)
        if f.lower().endswith(".pdf")
    ])

def resampled_face_locations(full_img):
    """
    Downsample full_img for detection, 
    then map face locations back to full_img coords.
    """
    w, h = full_img.size
    scale = max(w, h) / DETECT_MAX_DIM
    if scale < 1:
        # no resample needed
        small = full_img
        factor = 1.0
    else:
        sw = int(w / scale)
        sh = int(h / scale)
        small = full_img.resize((sw, sh), Image.LANCZOS)
        factor = scale

    arr_small = np.array(small)
    locs = face_recognition.face_locations(arr_small)
    # map back
    return [
        (
            int(top*factor),
            int(right*factor),
            int(bottom*factor),
            int(left*factor)
        )
        for top, right, bottom, left in locs
    ]

def extract_and_store():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    # ensure tables
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
    conn.execute("""
      CREATE TABLE IF NOT EXISTS processed_pdfs (
        pdf TEXT UNIQUE
      )
    """)
    conn.commit()

    pdfs = get_pdfs(PDF_FOLDER)
    pending = [p for p in pdfs
               if not conn.execute("SELECT 1 FROM processed_pdfs WHERE pdf=?", (p,)).fetchone()]

    if not pending:
        print("✅ No new PDFs.")
    else:
        print(f"🔄 Processing {len(pending)} PDFs sequentially:")
        for idx, pdf in enumerate(pending, 1):
            print(f"[{idx}/{len(pending)}] {os.path.basename(pdf)}")
            try:
                doc = fitz.open(pdf)
            except Exception as e:
                print(f"  ✖ Failed to open: {e}")
                continue

            base = os.path.splitext(os.path.basename(pdf))[0]
            batch = []

            for page_num, page in enumerate(doc, 1):
                try:
                    pix = page.get_pixmap()  # default zoom=1
                    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                except Exception as e:
                    print(f"  ✖ Page {page_num} render error: {e}")
                    continue

                # detect on downsampled
                locs = resampled_face_locations(img)
                # now get full-res encodings at those boxes
                arr_full = np.array(img)
                full_encs = face_recognition.face_encodings(arr_full, locs)

                for i, (loc, enc) in enumerate(zip(locs, full_encs), 1):
                    top, right, bottom, left = loc
                    w, h = right-left, bottom-top
                    pad_x = int(w * PADDING_RATIO)
                    pad_y = int(h * PADDING_RATIO)

                    x1 = max(left - pad_x, 0)
                    y1 = max(top  - pad_y, 0)
                    x2 = min(right + pad_x, img.width)
                    y2 = min(bottom+ pad_y, img.height)

                    crop = img.crop((x1,y1,x2,y2)).resize(TARGET_SIZE, Image.LANCZOS)
                    fn = f"{base}_p{page_num}_f{i}.jpg"
                    out_path = os.path.join(FACES_DIR, fn)
                    os.makedirs(FACES_DIR, exist_ok=True)
                    crop.save(out_path)

                    blob = np.array(enc, dtype=np.float64).tobytes()
                    batch.append((fn, out_path.replace("\\","/"), blob))

            # upsert this PDF’s faces
            cur = conn.cursor()
            for fn, ip, blob in batch:
                try:
                    cur.execute(
                        "INSERT INTO faces (filename,image_path,encoding) VALUES(?,?,?)",
                        (fn, ip, sqlite3.Binary(blob))
                    )
                except sqlite3.IntegrityError:
                    cur.execute(
                        "UPDATE faces SET image_path=?,encoding=? WHERE filename=?",
                        (ip, sqlite3.Binary(blob), fn)
                    )
            conn.commit()
            # mark done
            conn.execute("INSERT OR IGNORE INTO processed_pdfs(pdf) VALUES(?)", (pdf,))
            conn.commit()

    conn.close()

def rebuild_faiss():
    conn = sqlite3.connect(DB_PATH)
    idx = faiss.IndexFlatL2(128)
    filenames = []
    total = conn.execute("SELECT COUNT(*) FROM faces").fetchone()[0]
    print("🔨 Rebuilding FAISS index…")

    for offset in range(0, total, 1000):
        rows = conn.execute(
            "SELECT filename, encoding FROM faces ORDER BY id LIMIT ? OFFSET ?",
            (1000, offset)
        ).fetchall()
        mats = np.vstack([np.frombuffer(r[1], dtype=np.float64) for r in rows])
        idx.add(mats)
        filenames.extend(r[0] for r in rows)
        print(f"  • Indexed {min(offset+len(rows), total)}/{total}")

    faiss.write_index(idx, INDEX_PATH)
    with open(MAP_PATH, "wb") as f:
        pickle.dump(filenames, f)
    conn.close()
    print("✅ FAISS index saved to", INDEX_PATH)

if __name__ == "__main__":
    extract_and_store()
    rebuild_faiss()

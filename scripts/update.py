# Re-uploading the verbose version of the script after kernel reset.
import os
import pickle
import re
import sqlite3
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime

import face_recognition
import faiss
import fitz  # PyMuPDF
from PIL import Image
from tqdm import tqdm

import numpy as np

# CONFIG
DOWNLOADS_FOLDER = r"C:\Users\1439\Documents\DopplegangerApp\downloads"
FACES_DIR = r"C:\Users\1439\Documents\DopplegangerApp\static\extracted_faces"
DB_PATH = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"
INDEX_PATH = r"C:\Users\1439\Documents\DopplegangerApp\faces.index"
MAP_PATH = r"C:\Users\1439\Documents\DopplegangerApp\faces_filenames.pkl"
MAX_WORKERS = os.cpu_count() or 4
PADDING_RATIO = 0.25
TARGET_SIZE = (256, 256)

def ensure_tables():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS faces (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT UNIQUE,
        image_path TEXT,
        encoding BLOB,
        school TEXT,
        year TEXT,
        location TEXT,
        extracted_date TEXT,
        yearbook_year TEXT,
        school_name TEXT,
        page_number INTEGER,
        quality_score REAL,
        quality_flag TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS processed_pdfs (
        pdf TEXT PRIMARY KEY
    )""")
    conn.commit()
    conn.close()

def extract_faces_from_pdf_verbose(pdf_path):
    results = []
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        return [], os.path.basename(pdf_path), f"❌ Failed to open PDF: {e}"

    base = os.path.splitext(os.path.basename(pdf_path))[0]
    total_pages = len(doc)
    print(f"🔍 Processing {pdf_path} ({total_pages} pages)")
    for page_num, page in enumerate(doc, start=1):
        try:
            print(f"  ➤ Page {page_num}/{total_pages}")
            pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            arr = np.array(img)
            locs = face_recognition.face_locations(arr)
            encs = face_recognition.face_encodings(arr, locs)

            print(f"     → Found {len(encs)} faces")
            for i, (loc, enc) in enumerate(zip(locs, encs), start=1):
                top, right, bottom, left = loc
                w, h = right - left, bottom - top
                pad_x = int(w * PADDING_RATIO)
                pad_y = int(h * PADDING_RATIO)
                x1 = max(left - pad_x, 0)
                y1 = max(top - pad_y, 0)
                x2 = min(right + pad_x, img.width)
                y2 = min(bottom + pad_y, img.height)
                crop = img.crop((x1, y1, x2, y2)).resize(TARGET_SIZE, Image.LANCZOS)

                fn = f"{base}_p{page_num}_f{i}.jpg"
                out_path = os.path.join(FACES_DIR, fn)
                os.makedirs(FACES_DIR, exist_ok=True)
                crop.save(out_path)

                reencoded = face_recognition.face_encodings(np.array(crop))
                if not reencoded:
                    continue
                vec = reencoded[0].astype(np.float64)
                blob = vec.tobytes()
                extracted_date = datetime.now().isoformat()

                results.append((
                    fn,
                    out_path.replace("\\", "/"),
                    sqlite3.Binary(blob),
                    "", "", "", extracted_date,
                    "", "", page_num, None, None
                ))
        except Exception as e:
            print(f"     ⚠️ Error on page {page_num}: {e}")
            continue

    return results, os.path.basename(pdf_path), None

def insert_batch(conn, batch):
    c = conn.cursor()
    for row in batch:
        try:
            c.execute("""
                INSERT OR IGNORE INTO faces (
                    filename, image_path, encoding, school, year, location,
                    extracted_date, yearbook_year, school_name, page_number,
                    quality_score, quality_flag
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, row)
        except Exception:
            continue
    conn.commit()

def get_unprocessed_pdfs():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    all_pdfs = [os.path.join(DOWNLOADS_FOLDER, f) for f in os.listdir(DOWNLOADS_FOLDER) if f.lower().endswith(".pdf")]
    done = c.execute("SELECT pdf FROM processed_pdfs").fetchall()
    done_set = {row[0] for row in done}
    conn.close()
    return [p for p in all_pdfs if os.path.basename(p) not in done_set]

def mark_done(pdf_name):
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT OR IGNORE INTO processed_pdfs(pdf) VALUES(?)", (pdf_name,))
    conn.commit()
    conn.close()

def rebuild_faiss():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT filename, encoding FROM faces WHERE encoding IS NOT NULL")
    rows = c.fetchall()
    conn.close()

    if not rows:
        print("❌ No encodings found. Skipping FAISS index.")
        return

    index = faiss.IndexFlatL2(128)
    filenames = []
    for i in range(0, len(rows), 1000):
        chunk = rows[i:i+1000]
        vecs = [np.frombuffer(row[1], dtype=np.float64) for row in chunk]
        index.add(np.vstack(vecs))
        filenames.extend([row[0] for row in chunk])

    faiss.write_index(index, INDEX_PATH)
    with open(MAP_PATH, "wb") as f:
        pickle.dump(filenames, f)

def main():
    ensure_tables()
    pdfs = get_unprocessed_pdfs()
    if not pdfs:
        print("✅ No new PDFs found.")
        return

    print(f"🚀 Starting verbose extraction from {len(pdfs)} PDFs")
    for pdf_path in pdfs:
        batch, pdf_name, error = extract_faces_from_pdf_verbose(pdf_path)
        if error:
            print(error)
            continue
        if batch:
            conn = sqlite3.connect(DB_PATH)
            insert_batch(conn, batch)
            conn.close()
        mark_done(pdf_name)

    print("🔁 Rebuilding FAISS index...")
    rebuild_faiss()
    print("✅ DONE. Faces extracted, encoded, and indexed.")

if __name__ == "__main__":
    main()

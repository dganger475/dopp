
import pickle
import sqlite3

import faiss

import numpy as np

DB_PATH = "faces.db"
INDEX_PATH = "faces.index"
META_PATH = "faces_meta.pkl"

print("🔁 Rebuilding FAISS index from database...")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Load all non-blurry encodings
cursor.execute("SELECT id, filename, encoding, quality_flag FROM faces WHERE quality_flag != 'blurry'")
rows = cursor.fetchall()

if not rows:
    print("⚠️ No usable encodings found.")
    exit()

encodings = []
metadata = []

for row in rows:
    id_, filename, encoding_blob, flag = row
    try:
        encoding = np.frombuffer(encoding_blob, dtype=np.float64).astype(np.float32)
        if encoding.shape == (128,):
            encodings.append(encoding)
            metadata.append({
                "id": id_,
                "filename": filename,
                "flag": flag
            })
    except Exception as e:
        print(f"❌ Error decoding face ID {id_}: {e}")

if not encodings:
    print("❌ No valid encodings extracted.")
    exit()

enc_matrix = np.stack(encodings).astype(np.float32)
index = faiss.IndexFlatL2(128)
index.add(enc_matrix)

faiss.write_index(index, INDEX_PATH)
with open(META_PATH, "wb") as f:
    pickle.dump(metadata, f)

print(f"✅ Rebuilt index with {len(encodings)} faces (excluding blurry).")

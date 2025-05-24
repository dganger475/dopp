
import pickle
import sqlite3

import faiss

import numpy as np

DB_PATH = "faces.db"
INDEX_PATH = "faces.index"
META_PATH = "faces_meta.pkl"

def build_faiss_index():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename, encoding FROM faces WHERE encoding IS NOT NULL")
    entries = cursor.fetchall()
    conn.close()

    if not entries:
        print("No encodings found in database.")
        return

    dim = 128  # face_recognition encodings are 128-D
    index = faiss.IndexFlatL2(dim)
    metadata = []

    for entry in entries:
        id_, filename, encoding_blob = entry
        try:
            encoding = np.frombuffer(encoding_blob, dtype=np.float64)
            if encoding.shape[0] != 128:
                continue
            index.add(np.expand_dims(encoding.astype('float32'), axis=0))
            metadata.append({"id": id_, "filename": filename})
        except Exception as e:
            print(f"Failed to process {filename}: {e}")

    faiss.write_index(index, INDEX_PATH)
    with open(META_PATH, "wb") as f:
        pickle.dump(metadata, f)

    print(f"FAISS index built with {index.ntotal} entries.")

if __name__ == "__main__":
    build_faiss_index()

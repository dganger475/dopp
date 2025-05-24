#!/usr/bin/env python3

import os
import pickle
import sqlite3

import faiss

import numpy as np

from app_config import DB_PATH, EXTRACTED_FACES, INDEX_PATH, MAP_PATH

# ─── CONFIG ─────────────────────────────────────────────────────────────────────
# ────────────────────────────────────────────────────────────────────────────────

def cleanup_backups():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # find all backup entries
    rows = c.execute(
        "SELECT filename, image_path FROM faces WHERE filename LIKE 'backup/%'"
    ).fetchall()

    print(f"Found {len(rows)} backup entries. Deleting…")
    for fn, img_path in rows:
        full_path = os.path.join(EXTRACTED_FACES, fn)
        if os.path.exists(full_path):
            os.remove(full_path)
        # remove from DB
        c.execute("DELETE FROM faces WHERE filename = ?", (fn,))

    conn.commit()
    conn.close()

def rebuild_faiss():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # load remaining embeddings
    rows = c.execute("SELECT filename, encoding FROM faces ORDER BY id").fetchall()
    filenames = [r[0] for r in rows]
    mats = np.vstack([np.frombuffer(r[1], dtype=np.float64) for r in rows])

    # build index
    idx = faiss.IndexFlatL2(mats.shape[1])
    idx.add(mats)
    faiss.write_index(idx, INDEX_PATH)

    # save filename map
    with open(MAP_PATH, "wb") as f:
        pickle.dump(filenames, f)

    conn.close()
    print(f"✅ Rebuilt FAISS index ({len(filenames)} faces)")

if __name__ == "__main__":
    cleanup_backups()
    rebuild_faiss()

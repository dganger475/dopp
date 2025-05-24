import json
import os

import cv2
from insightface.app import FaceAnalysis
from tqdm import tqdm

import numpy as np

# --- CONFIG ---
TOP_MATCHES_DIR = "top_matches_reformatted"
EXTRACTED_FACES_DIR = "static/extracted_faces"
OUTPUT_DIR = "insight_embeddings"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- INIT INSIGHTFACE ---
app = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
app.prepare(ctx_id=0)

def encode_images(name):
    json_path = os.path.join(TOP_MATCHES_DIR, f"{name}_top1000.json")
    with open(json_path, "r") as f:
        data = json.load(f)

    encoded = []
    for entry in tqdm(data, desc=f"🔁 Encoding top matches for {name}"):
        rel_path = entry["image_path"]
        img_path = os.path.join(EXTRACTED_FACES_DIR, rel_path)
        if not os.path.exists(img_path):
            print(f"❌ Missing: {img_path}")
            continue

        img = cv2.imread(img_path)
        if img is None:
            print(f"❌ Unreadable: {img_path}")
            continue

        faces = app.get(img)
        if not faces:
            continue

        embedding = faces[0].embedding.astype(np.float32)
        encoded.append({
            "filename": rel_path,
            "embedding": embedding.tolist()
        })

    output_file = os.path.join(OUTPUT_DIR, f"{name}_insight_embeddings.json")
    with open(output_file, "w") as f:
        json.dump(encoded, f)
    print(f"✅ Encoded {len(encoded)} faces for {name}")
    print(f"💾 Saved to {output_file}")

if __name__ == "__main__":
    encode_images("me")
    encode_images("wife")

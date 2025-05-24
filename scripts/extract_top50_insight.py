import json
import os

TOP_MATCHES_DIR = "top_matches"
FIXED_EMBEDDINGS_DIR = "insight_embeddings_fixed"
OUTPUT_DIR = "insight_embeddings"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_embeddings(path):
    with open(path, "r") as f:
        return json.load(f)

def extract_top50(person):
    matches_path = os.path.join(TOP_MATCHES_DIR, f"{person}_top1000.json")
    embeddings_path = os.path.join(FIXED_EMBEDDINGS_DIR, f"{person}_insight_embeddings.json")
    output_path = os.path.join(OUTPUT_DIR, f"{person}_top50_insight.json")

    with open(matches_path, "r") as f:
        top_matches = json.load(f)

    embeddings = load_embeddings(embeddings_path)

    top50 = []
    for item in top_matches[:50]:
        filename = item[0]
        if filename in embeddings:
            top50.append({
                "filename": filename,
                "embedding": embeddings[filename]
            })
        else:
            print(f"⚠️ Missing embedding for: {filename}")

    with open(output_path, "w") as f:
        json.dump(top50, f, indent=2)

    print(f"✅ Saved top 50 insight matches to: {output_path}")

# Run for both users
extract_top50("me")
extract_top50("wife")

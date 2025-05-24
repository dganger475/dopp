import os
import sqlite3
from pathlib import Path

from PIL import Image, ImageFilter, ImageStat
from tqdm import tqdm

from app_config import DB_PATH, EXTRACTED_FACES

# Configuration
QUALITY_THRESHOLD = 50  # Tune this value based on observed results

def assess_image_quality(image_path):
    try:
        img = Image.open(image_path).convert("RGB")
        gray = img.convert("L")
        stat = ImageStat.Stat(gray)

        contrast = stat.stddev[0]
        brightness = stat.mean[0]
        sharpness = ImageStat.Stat(img.filter(ImageFilter.FIND_EDGES)).stddev[0]

        # Weighted quality score
        quality = round((sharpness * 2 + contrast + brightness / 4), 2)
        return quality
    except Exception as e:
        print(f"Error processing {image_path.name}: {e}")
        return None

def main():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("🔍 Assessing face image quality...")
    results = []

    for file in tqdm(EXTRACTED_FACES.glob("*.jpg")):
        quality = assess_image_quality(file)
        if quality is not None:
            results.append((file.name, quality))

    results.sort(key=lambda x: x[1])

    # Save to a table
    cursor.execute("DROP TABLE IF EXISTS face_quality")
    cursor.execute("""
        CREATE TABLE face_quality (
            filename TEXT PRIMARY KEY,
            quality_score REAL
        )
    """)
    cursor.executemany("INSERT INTO face_quality (filename, quality_score) VALUES (?, ?)", results)
    conn.commit()
    conn.close()

    print(f"\n✅ Rated {len(results)} face images.")
    print("📉 Lowest 10 by quality:")
    for fname, score in results[:10]:
        print(f"{score:.2f} - {fname}")

if __name__ == "__main__":
    main()

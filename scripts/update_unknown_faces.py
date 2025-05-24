
import os
import sqlite3

from PIL import Image, ImageEnhance, ImageFilter, ImageStat

import numpy as np

DB_PATH = "faces.db"

def assess_image_quality(image):
    gray = image.convert('L')
    stat = ImageStat.Stat(gray)
    contrast = stat.stddev[0]
    brightness = stat.mean[0]
    sharpness = ImageStat.Stat(image.filter(ImageFilter.FIND_EDGES)).stddev[0]
    score = (sharpness * 0.5) + (contrast * 0.3) + (brightness / 255 * 0.2)

    if sharpness < 5:
        flag = "blurry"
    elif contrast < 15:
        flag = "low_contrast"
    elif brightness < 40:
        flag = "dark"
    else:
        flag = "good"

    return score, flag

def update_unknown_faces():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, image_path FROM faces WHERE quality_flag IS NULL OR quality_flag = 'unknown'")
    rows = cursor.fetchall()

    print(f"🔍 Found {len(rows)} faces with unknown quality. Updating...")

    updated = 0
    for face_id, image_path in rows:
        if not os.path.exists(image_path):
            print(f"⚠️ Image not found: {image_path}")
            continue

        try:
            img = Image.open(image_path).convert("RGB")
            score, flag = assess_image_quality(img)
            cursor.execute("UPDATE faces SET quality_score = ?, quality_flag = ? WHERE id = ?",
                           (score, flag, face_id))
            updated += 1
            if updated % 500 == 0:
                print(f"✅ Updated {updated} entries...")
        except Exception as e:
            print(f"❌ Failed to process {image_path}: {e}")

    conn.commit()
    conn.close()
    print(f"✅ Finished. {updated} unknown entries updated with quality info.")

if __name__ == "__main__":
    update_unknown_faces()

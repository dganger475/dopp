
import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import face_recognition
from PIL import Image, ImageFilter, ImageStat
from tqdm import tqdm

import numpy as np

FACES_FOLDER = Path("static/extracted_faces")
MIN_SHARPNESS = 5
MIN_CONTRAST = 12
MIN_BRIGHTNESS = 40
MAX_WORKERS = os.cpu_count() or 4

def assess_image_quality(image):
    gray = image.convert('L')
    stat = ImageStat.Stat(gray)
    contrast = stat.stddev[0]
    brightness = stat.mean[0]
    sharpness = ImageStat.Stat(image.filter(ImageFilter.FIND_EDGES)).stddev[0]

    if sharpness < MIN_SHARPNESS:
        return "blurry"
    elif contrast < MIN_CONTRAST:
        return "low_contrast"
    elif brightness < MIN_BRIGHTNESS:
        return "dark"
    return "good"

def analyze_image(img_path_str):
    img_path = Path(img_path_str).resolve()
    try:
        img = Image.open(img_path).convert("RGB")
        quality = assess_image_quality(img)

        if quality == "blurry":
            return ("delete", str(img_path))

        img_array = np.array(img)
        encodings = face_recognition.face_encodings(img_array)

        if not encodings or len(encodings[0]) != 128:
            return ("delete", str(img_path))

        return ("keep", str(img_path))

    except Exception:
        return ("error", str(img_path))

def clean_extracted_faces_multiprocessing():
    images = list(FACES_FOLDER.glob("*.jpg"))
    print(f"🔍 Found {len(images)} face images to scan using {MAX_WORKERS} processes...")

    to_delete = []
    results = {"keep": 0, "delete": 0, "error": 0}

    with ProcessPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(analyze_image, str(img)): img for img in images}
        for f in tqdm(as_completed(futures), total=len(futures), desc="Scanning", unit="img"):
            result, path = f.result()
            if result == "keep":
                results["keep"] += 1
            elif result == "delete":
                results["delete"] += 1
                to_delete.append(path)
            else:
                results["error"] += 1
                tqdm.write(f"❌ Error: {Path(path).name}")

    print("\n🧾 Summary:")
    print(f"  Kept   : {results['keep']}")
    print(f"  Deleted: {results['delete']}")
    print(f"  Failed : {results['error']}")

    confirm = input("\n⚠️  Delete the {0} flagged files now? (y/n): ".format(results["delete"]))
    if confirm.lower() == "y":
        for path in tqdm(to_delete, desc="Deleting", unit="file"):
            try:
                Path(path).unlink()
            except Exception as e:
                tqdm.write(f"❌ Failed to delete {Path(path).name}: {e}")
        print("✅ Cleanup complete.")
    else:
        print("❌ Deletion cancelled. No files were removed.")

if __name__ == "__main__":
    clean_extracted_faces_multiprocessing()

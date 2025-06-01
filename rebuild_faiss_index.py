import os
import csv
import numpy as np
import faiss
import face_recognition

# Config
IMAGE_DIR = "path_to_local_images"  # Replace with your local image dir for renamed files
MAPPING_CSV = "b2_supabase_faiss_mapping.csv"
INDEX_OUTPUT = "faces_index.faiss"
IDS_OUTPUT = "face_ids.npy"

# Load mapping
face_encodings = []
face_ids = []

with open(MAPPING_CSV, newline="") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        new_filename = row["new_filename"]
        image_path = os.path.join(IMAGE_DIR, new_filename)

        try:
            image = face_recognition.load_image_file(image_path)
            encodings = face_recognition.face_encodings(image)
            if encodings:
                face_encodings.append(encodings[0])
                face_ids.append(new_filename)
                print(f"Encoded: {new_filename}")
            else:
                print(f"No face found in {new_filename}")
        except Exception as e:
            print(f"Error processing {new_filename}: {e}")

# Build FAISS index
if face_encodings:
    dim = 128
    index = faiss.IndexFlatL2(dim)
    index.add(np.array(face_encodings, dtype='float32'))
    faiss.write_index(index, INDEX_OUTPUT)
    np.save(IDS_OUTPUT, np.array(face_ids))
    print("FAISS index and IDs saved.")
else:
    print("No encodings were added to the index.")

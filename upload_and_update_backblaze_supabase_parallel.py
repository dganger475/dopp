import os
import backblaze_b2
import supabase
import pandas as pd
from supabase import create_client
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

B2_KEY_ID = os.getenv("B2_KEY_ID")
B2_APP_KEY = os.getenv("B2_APP_KEY")
B2_BUCKET = os.getenv("B2_BUCKET")
B2_FOLDER = "faces"

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_TABLE = "faces"

FOLDERS = [
    r"C:\Users\1439\Documents\Dopp\static\extracted_faces",
    r"C:\Users\1439\Documents\Dopp\static\profile_pics"
]

MAPPING_CSV = "b2_supabase_faiss_mapping.csv"

# Initialize Supabase client
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize Backblaze client
b2 = backblaze_b2.B2(key_id=B2_KEY_ID, application_key=B2_APP_KEY)
bucket = b2.get_bucket_by_name(B2_BUCKET)

# Load mapping file
df = pd.read_csv(MAPPING_CSV)
rename_map = dict(zip(df["old_filename"], df["new_filename"]))

def process_file(folder, filename):
    full_path = os.path.join(folder, filename)
    if not os.path.isfile(full_path):
        return f"Skipped: {filename} (not a file)"

    new_filename = rename_map.get(filename, filename)
    try:
        with open(full_path, "rb") as f:
            bucket.upload_bytes(f.read(), f"{B2_FOLDER}/{new_filename}")
        print(f"Uploaded: {new_filename}")

        response = supabase_client.table(SUPABASE_TABLE).update(
            {"filename": new_filename}).eq("filename", filename).execute()
        if response.get("status_code", 200) >= 400:
            return f"Supabase update failed for {filename}: {response}"
        else:
            return f"Supabase updated for {filename} -> {new_filename}"
    except Exception as e:
        return f"Error with {filename}: {e}"

# Gather all files to process
tasks = []
for folder in FOLDERS:
    for fname in os.listdir(folder):
        tasks.append((folder, fname))

# Run with ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=15) as executor:
    futures = [executor.submit(process_file, folder, fname) for folder, fname in tasks]
    for future in as_completed(futures):
        print(future.result())

print("All uploads and updates completed.")

import os
import pandas as pd

# Load CSV with filenames to delete
csv_path = "estimated_deleted_filenames_TX_IL.csv"
df = pd.read_csv(csv_path)
filenames = df['new_filename'].tolist()

# Folder containing face images
folder = r"C:\Users\1439\Documents\Dopp\static\extracted_faces"

# Logging setup
deleted = []
not_found = []

for filename in filenames:
    path = os.path.join(folder, filename)
    if os.path.exists(path):
        try:
            os.remove(path)
            deleted.append(filename)
        except Exception as e:
            print(f"Error deleting {filename}: {e}")
    else:
        not_found.append(filename)

# Log results
with open("deleted_faces_log.txt", "w") as f:
    f.write("Deleted files:\n")
    f.writelines(f + "\n" for f in deleted)
    f.write("\nNot found files:\n")
    f.writelines(f + "\n" for f in not_found)

print(f"Done. Deleted: {len(deleted)}, Not Found: {len(not_found)}")

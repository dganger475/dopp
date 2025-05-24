import os
import sqlite3

backup_folder = r"C:\Users\1439\Documents\DopplegangerApp\backup_db"
target_table = "faces"

def get_counts(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {target_table}")
        total = cursor.fetchone()[0]
        cursor.execute(f"SELECT COUNT(*) FROM {target_table} WHERE embedding_insightface IS NOT NULL")
        with_embeddings = cursor.fetchone()[0]
        conn.close()
        return total, with_embeddings
    except Exception as e:
        return None, None

print("🔍 Scanning backup DBs...\n")
for file in os.listdir(backup_folder):
    if file.endswith(".db"):
        full_path = os.path.join(backup_folder, file)
        total, embeddings = get_counts(full_path)
        if total is not None:
            print(f"📁 {file}: {total:,} rows, {embeddings:,} with embeddings")
        else:
            print(f"❌ {file}: Error reading DB")

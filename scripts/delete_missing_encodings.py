import sqlite3

DATABASE_FILE = r"C:\Users\1439\Documents\DopplegangerApp\faces.db"

def delete_missing_encodings():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Delete all entries where encoding is NULL or empty
    cursor.execute("DELETE FROM faces WHERE encoding IS NULL OR encoding = ''")
    conn.commit()
    
    print(f"✅ Deleted {cursor.rowcount} entries with missing encodings.")

    conn.close()

delete_missing_encodings()

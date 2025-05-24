import logging
import os
import sqlite3

from app_config import DB_PATH, SORTED_FACES

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def connect_db():
    """Connect to the SQLite database."""
    try:
        conn = sqlite3.connect(DB_PATH)
        return conn
    except sqlite3.Error as e:
        logging.error(f"Database Connection Error: {e}", exc_info=True)
        return None

def fix_database_entries():
    """Correct filenames and file paths in the database."""
    conn = connect_db()
    if conn is None:
        return

    cursor = conn.cursor()

    # Fetch all database entries
    cursor.execute("SELECT filename, image_path, year, school, location, page_number, gender, race FROM faces")
    rows = cursor.fetchall()

    for old_filename, old_path, year, school, location, page_number, gender, race in rows:
        # Ensure valid values
        gender = gender if gender else "Unknown"
        race = race.replace(" ", "_").capitalize() if race else "Unknown"
        page_number = str(page_number) if page_number and page_number != "None" else "1"  # Ensure no "None" values

        # Construct the correct filename with full path
        new_filename = f"{year}_{school.replace(' ', '_')}_{location.replace(' ', '_')}_page_{page_number}_face.jpg"
        new_path = os.path.join(SORTED_FACES, gender, race, new_filename)
        new_db_filename = f"sorted_faces/{gender}/{race}/{new_filename}"

        # Ensure directory exists
        os.makedirs(os.path.dirname(new_path), exist_ok=True)

        # Move file if it exists at the old path
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            logging.info(f"✅ Moved: {old_path} -> {new_path}")
        else:
            logging.warning(f"⚠️ File not found: {old_path}")

        # Fix the database update with correct file path
        try:
            cursor.execute("UPDATE faces SET filename=?, image_path=? WHERE filename=?", 
                           (new_db_filename, new_path, old_filename))
            conn.commit()
        except sqlite3.IntegrityError:
            logging.warning(f"⚠️ Duplicate filename detected: {new_db_filename}")
    
    conn.close()
    logging.info("✅ Database file paths fixed successfully!")

if __name__ == "__main__":
    fix_database_entries()

import logging
import os
import sys

from flask import Flask

from utils.face.recognition import rebuild_faiss_index

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Create a minimal Flask app to provide configuration
app = Flask(__name__)
app.config.update(
    DB_PATH="faces.db",  # Main faces database in root
    INDEX_PATH="faces.index",
    MAP_PATH="faces_filenames.pkl"
)

def main():
    logging.info("Starting FAISS index rebuild process...")
    
    # Confirm files exist
    db_path = app.config['DB_PATH']
    if not os.path.exists(db_path):
        logging.error(f"Database file not found: {db_path}")
        return False
    
    logging.info(f"Using database: {db_path}")
    logging.info(f"Will create index at: {app.config['INDEX_PATH']}")
    logging.info(f"Will create mapping at: {app.config['MAP_PATH']}")
    
    # Rebuild the FAISS index
    success = rebuild_faiss_index(app)
    
    if success:
        logging.info("✅ FAISS index successfully rebuilt!")
        return True
    else:
        logging.error("❌ Failed to rebuild FAISS index")
        return False

if __name__ == "__main__":
    if main():
        sys.exit(0)
    else:
        sys.exit(1)

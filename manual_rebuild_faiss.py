import logging
import os
import sys

# Add project root to Python path to allow imports from 'utils', 'models', etc.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, project_root)

from flask import Flask

# Now try to import the function
from utils.face.recognition import rebuild_faiss_index
# We will not import Config from config.py for path settings in this script
# to ensure explicit control during manual rebuild.

def run_rebuild():
    """Initializes a minimal Flask app context and runs the FAISS index rebuild."""
    print("Starting FAISS index rebuild process...")
    
    # Configure basic logging to see output from the rebuild function
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    # Create a minimal Flask app
    app = Flask(__name__)
    
    # --- Explicitly define paths for the rebuild script ---
    # project_root is already defined as: os.path.abspath(os.path.join(os.path.dirname(__file__)))
    # This means project_root = C:\Users\dumpy\Documents\Dopp
    
    # Correct path to the large database
    correct_db_path = os.path.join(project_root, 'faces.db') 
    
    # Standard paths for index and map, typically in a 'data/index' subdirectory
    # If your main app stores them elsewhere, these should match that location.
    data_dir_for_index = os.path.join(project_root, 'data') # e.g., C:\Users\dumpy\Documents\Dopp\data
    index_dir = os.path.join(data_dir_for_index, 'index')   # e.g., C:\Users\dumpy\Documents\Dopp\data\index
    os.makedirs(index_dir, exist_ok=True) # Ensure directory exists
    
    correct_index_path = os.path.join(index_dir, 'faces.index')
    correct_map_path = os.path.join(index_dir, 'faces_filenames.pkl')

    # Set these paths directly into the app.config for this script's context
    app.config['DB_PATH'] = correct_db_path
    app.config['INDEX_PATH'] = correct_index_path
    app.config['MAP_PATH'] = correct_map_path

    # Ensure the DB_PATH environment variable is also set, as some parts might use it as a fallback
    os.environ['DB_PATH'] = app.config['DB_PATH']

    logging.info(f"SCRIPT OVERRIDE - Using DB_PATH: {app.config['DB_PATH']}")
    logging.info(f"Using INDEX_PATH: {app.config['INDEX_PATH']}")
    logging.info(f"Using MAP_PATH: {app.config['MAP_PATH']}")

    if not os.path.exists(app.config['DB_PATH']):
        logging.error(f"Database file not found at configured DB_PATH: {app.config['DB_PATH']}")
        logging.error("Please ensure the path is correct in config.py or in this script.")
        return

    with app.app_context():
        logging.info("Flask app context created. Calling rebuild_faiss_index...")
        success = rebuild_faiss_index(app=app)
        if success:
            logging.info("FAISS index rebuild process completed successfully.")
        else:
            logging.error("FAISS index rebuild process failed. Check logs for details.")

if __name__ == "__main__":
    run_rebuild()

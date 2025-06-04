"""
Startup utilities for DoppleGanger Flask app.
Handles DB setup, FAISS index (re)building, default images, and model file checks.
"""

import os
import sys
import importlib
import logging

from utils.db.database import setup_users_db, init_app
from utils.face.recognition import rebuild_faiss_index
from utils.index.faiss_manager import faiss_index_manager
from utils.db.migrations import run_migrations
from utils.model_loader import ensure_model_files

logger = logging.getLogger(__name__)

def run_startup_tasks(app):
    """
    Run all startup tasks needed before launching the Flask app.
    - Sets up user and face databases
    - Applies necessary database migrations
    - Checks and (re)builds FAISS index if needed
    - Creates default images if missing
    - Ensures all required model files are present
    """
    logger.info("Running startup tasks...")
    
    # 1. Setup initial database tables (idempotent)
    logger.info("Ensuring base database tables are set up...")
    init_app(app)  # Initialize SQLAlchemy
    setup_users_db()  # Create tables
    logger.info("Base database table setup check complete.")

    # 2. Apply database migrations (idempotent)
    logger.info("Applying database migrations...")
    run_migrations()

    # --- FAISS Index Initialization ---
    if not os.path.exists(app.config["INDEX_PATH"]) \
        or not os.path.exists(app.config["MAP_PATH"]):
        logger.info("FAISS index not found. Building initial index...")
        with app.app_context():
            db_path = os.path.join(app.root_path, "faces.db")
            app.config["DB_PATH"] = db_path
            logger.info(
                "Using consistent database path for FAISS index rebuild: "
                + db_path
            )

            os.environ["DB_PATH"] = os.path.abspath(db_path)
            os.environ["INDEX_PATH"] = os.path.abspath(app.config["INDEX_PATH"])
            os.environ["MAP_PATH"] = os.path.abspath(app.config["MAP_PATH"])

            logger.info("Set environment variables:")
            logger.info("  DB_PATH = " + os.environ["DB_PATH"])
            logger.info("  INDEX_PATH = " + os.environ["INDEX_PATH"])
            logger.info("  MAP_PATH = " + os.environ["MAP_PATH"])

            logger.info("Starting FAISS index rebuild...")
            try:
                result = rebuild_faiss_index(app=app)
                if result:
                    logger.info("FAISS index rebuilt successfully")
                else:
                    logger.error("Failed to rebuild FAISS index")
            except Exception as e:
                logger.error(
                    "Exception during FAISS index rebuild: " + str(e)
                )
    else:
        logger.info("FAISS index will be loaded on demand")

    # --- Model Files ---
    try:
        if ensure_model_files():
            logger.info("All required model files are available")
        else:
            logger.warning("Some required model files are missing")
    except Exception as e:
        logger.error(f"Failed to check/download model files: {e}")

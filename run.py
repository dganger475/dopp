"""
Main entry point for the DoppleGanger application.
This is the recommended way to run the application.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def create_and_configure_app():
    """Create and configure the Flask application."""
    try:
        from app import create_app
        app = create_app()

        # --- CORS FIX: Add this block so frontend (local or ngrok) can talk to backend ---
        from flask_cors import CORS
        CORS(app, origins=[
            "http://localhost:5173",
            "https://7964-149-36-48-146.ngrok-free.app"
        ])
        # -------------------------------------------------------------------------------

        return app
    except Exception as e:
        logger.exception("Failed to create application")
        raise

def main():
    """Run the application."""
    try:
        # Create and configure the app
        app = create_and_configure_app()
        
        # Get debug setting from environment or config
        debug = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true' or app.config.get('DEBUG', False)
        
        # Log configuration
        logger.info("Starting application in %s mode", 'debug' if debug else 'production')
        logger.info("Database URI: %s", app.config.get('SQLALCHEMY_DATABASE_URI'))
        
        # Run the application
        app.run(
            host="0.0.0.0", 
            port=5001, 
            debug=debug, 
            use_reloader=debug,
            use_debugger=debug,
            use_evalex=debug
        )
    except Exception as e:
        logger.exception("Failed to start application")
        sys.exit(1)

if __name__ == "__main__":
    main()
"""
Startup script for DoppleGänger
==============================

Handles initialization of services and starts the application.
"""

import os
import sys
import time
import logging
import subprocess
import socket
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def wait_for_redis(host='localhost', port=6379, timeout=30):
    """Wait for Redis to become available."""
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((host, port))
            sock.close()
            logger.info("Redis is available")
            return True
        except socket.error:
            time.sleep(1)
    logger.error("Redis did not become available in time")
    return False

def start_redis():
    """Start Redis server."""
    try:
        # Create necessary directories
        Path('/var/run/redis').mkdir(parents=True, exist_ok=True)
        Path('/var/log/redis').mkdir(parents=True, exist_ok=True)
        
        # Start Redis server
        subprocess.run(['service', 'redis-server', 'start'], check=True)
        logger.info("Redis server started")
        
        # Wait for Redis to be available
        if not wait_for_redis():
            logger.error("Failed to connect to Redis")
            sys.exit(1)
            
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to start Redis: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error starting Redis: {e}")
        sys.exit(1)

def main():
    """Main entry point."""
    try:
        # Start Redis if in production
        if os.getenv('FLASK_ENV') == 'production':
            start_redis()
        
        # Import and create app
        from app import create_app
        app = create_app()
        
        # Run the app
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)))
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main() 
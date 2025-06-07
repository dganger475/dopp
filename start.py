import os
import sys
import time
import logging
import socket
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_port(port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("0.0.0.0", port))
        sock.close()
        return True
    except socket.error:
        return False

def main():
    logger.info("Starting application...")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info("Directory contents:")
    logger.info(os.listdir("."))
    logger.info("Environment variables:")
    for key, value in os.environ.items():
        logger.info(f"{key}={value}")

    # Start Redis server
    logger.info("Starting Redis server...")
    try:
        redis_process = subprocess.Popen(
            ["redis-server", "--daemonize", "yes"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        redis_process.wait(timeout=5)
        logger.info("Redis server started successfully")
    except Exception as e:
        logger.error(f"Failed to start Redis server: {e}")
        sys.exit(1)

    # Check if port is available
    port = int(os.getenv("PORT", 5000))
    logger.info(f"Checking if port {port} is available...")
    if not check_port(port):
        logger.error(f"Port {port} is already in use")
        sys.exit(1)
    logger.info(f"Port {port} is available")

    # Start gunicorn
    logger.info("Starting gunicorn...")
    cmd = [
        "gunicorn",
        "--bind", f"0.0.0.0:{port}",
        "--workers", "1",
        "--worker-class", "gevent",
        "--timeout", "120",
        "--access-logfile", "-",
        "--error-logfile", "-",
        "--log-level", "debug",
        "--preload",
        "app:app"
    ]

    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        logger.error(f"Gunicorn failed to start: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 
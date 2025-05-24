#!/usr/bin/env python
"""Test environment variable loading."""
import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Print key environment variables
print(f"SECRET_KEY: {os.environ.get('SECRET_KEY')}")
print(f"FLASK_ENV: {os.environ.get('FLASK_ENV')}")
print(f"DB_PATH: {os.environ.get('DB_PATH')}")
print(f"INDEX_PATH: {os.environ.get('INDEX_PATH')}")
print(f"UPLOAD_FOLDER: {os.environ.get('UPLOAD_FOLDER')}")

# Test config module
try:
    from config import config
    print("\nConfig module test:")
    print(f"Development config SECRET_KEY: {config['development'].SECRET_KEY}")
    print(f"Production config SECRET_KEY: {config['production'].SECRET_KEY}")
    print(f"Development config DB_PATH: {config['development'].DB_PATH}")
    print(f"Development config UPLOAD_FOLDER: {config['development'].UPLOAD_FOLDER}")
except Exception as e:
    print(f"Error importing config module: {e}")

#!/bin/bash
# exit on error
set -e

# Install minimal system dependencies first
apt-get update && apt-get install -y \
    build-essential \
    cmake \
    pkg-config \
    libx11-dev \
    libatlas-base-dev \
    libgtk-3-dev \
    libboost-python-dev \
    python3-venv \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
python3 -m venv /opt/venv
. /opt/venv/bin/activate

# Upgrade pip and install wheel without caching
pip install --no-cache-dir --upgrade pip
pip install --no-cache-dir wheel setuptools

# Install dlib from pre-built wheel first (without dependencies)
pip install --no-cache-dir --no-deps https://github.com/jloh02/dlib/releases/download/v19.22/dlib-19.22.1-cp310-cp310-linux_x86_64.whl

# Install core dependencies first
pip install --no-cache-dir flask gunicorn

# Install other dependencies in smaller batches
pip install --no-cache-dir numpy
pip install --no-cache-dir face-recognition
pip install --no-cache-dir -r requirements.txt

# Clean up pip cache
rm -rf ~/.cache/pip

# Ensure virtual environment is activated when running the app
echo "source /opt/venv/bin/activate" >> /etc/profile.d/venv.sh 
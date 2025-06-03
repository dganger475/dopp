#!/usr/bin/env bash
# exit on error
set -o errexit

# Install system dependencies
apt-get update
apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libx11-dev \
    libatlas-base-dev \
    libgtk-3-dev \
    libboost-python-dev \
    libpq-dev \
    python3-venv

# Create and activate virtual environment
python3 -m venv /opt/venv
. /opt/venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install dlib==19.22.1
pip install -r requirements.txt

# Make sure the virtual environment is used when running the app
echo "source /opt/venv/bin/activate" >> /etc/profile.d/venv.sh 
#!/bin/bash
apt-get update && apt-get install -y \
    cmake \
    build-essential \
    pkg-config \
    libx11-dev \
    libatlas-base-dev \
    libgtk-3-dev \
    libboost-python-dev \
    python3-dev \
    python3-pip \
    python3-numpy \
    python3-scipy \
    python3-pillow \
    python3-dlib

pip install --no-cache-dir -r requirements.txt 
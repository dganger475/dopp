#!/bin/bash
apt-get update && apt-get install -y \
    python3-dev \
    python3-pip \
    python3-numpy \
    python3-pillow

pip install --no-cache-dir -r requirements.txt 
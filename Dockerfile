# Use Python 3.10 base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=8080 \
    CMAKE_ARGS="-DUSE_AVX_INSTRUCTIONS=ON -DUSE_SSE4_INSTRUCTIONS=ON -DUSE_SSE2_INSTRUCTIONS=ON" \
    FORCE_CMAKE=1 \
    DLIB_USE_CUDA=0 \
    PIP_NO_CACHE_DIR=1

# Create and set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    pkg-config \
    libx11-dev \
    libatlas-base-dev \
    libgtk-3-dev \
    libboost-all-dev \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
    libpq-dev \
    libopenblas-dev \
    liblapack-dev \
    git \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dlib and face-recognition
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy && \
    pip install --no-cache-dir cmake && \
    wget https://github.com/jloh02/dlib/releases/download/v19.24/dlib-19.24.0-cp310-cp310-linux_x86_64.whl && \
    pip install --no-cache-dir dlib-19.24.0-cp310-cp310-linux_x86_64.whl && \
    pip install --no-cache-dir face-recognition==1.3.0

# Install other Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Create necessary directories
RUN mkdir -p /app/instance /app/flask_session /app/uploads

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "app:app"] 
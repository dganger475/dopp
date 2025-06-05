# Use Python 3.10 base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5000 \
    HOST=0.0.0.0 \
    CMAKE_ARGS="-DUSE_AVX_INSTRUCTIONS=ON -DUSE_SSE4_INSTRUCTIONS=ON -DUSE_SSE2_INSTRUCTIONS=ON -DUSE_SSE_INSTRUCTIONS=ON -DUSE_MMX_INSTRUCTIONS=ON -DUSE_BLAS=ON -DUSE_LAPACK=ON -DUSE_CUDA=OFF -DCMAKE_POLICY_VERSION_MINIMUM=3.5" \
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
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/*

# Copy frontend files and build
COPY frontend/package*.json ./frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ .
RUN npm run build

# Go back to main directory
WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir cmake==3.25.0 && \
    pip install --no-cache-dir wheel && \
    pip install --no-cache-dir setuptools && \
    pip install --no-cache-dir numpy && \
    pip install --no-cache-dir PyJWT==2.8.0 && \
    pip install --no-cache-dir dlib==19.22.0 && \
    pip install --no-cache-dir face-recognition==1.3.0 && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir PyJWT==2.8.0 --force-reinstall

# Create necessary directories
RUN mkdir -p /app/instance /app/flask_session /app/uploads

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

# Run gunicorn with explicit host binding
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "--log-level", "info", "app:app"] 
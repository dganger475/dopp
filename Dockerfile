# Use Python 3.10 base image
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=5000 \
    HOST=0.0.0.0 \
    PYTHONPATH=/app \
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
    netcat-traditional \
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
    pip install --no-cache-dir PyJWT==2.8.0 --force-reinstall && \
    pip install --no-cache-dir gevent==23.9.1 && \
    pip install --no-cache-dir gunicorn==21.2.0

# Create necessary directories
RUN mkdir -p /app/instance /app/flask_session /app/uploads /app/data/rate_limits

# Copy application files
COPY . .

# Create non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

USER appuser

# Expose the port
EXPOSE 5000

# Create a startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for port 5000 to be available..."\n\
while ! nc -z localhost 5000; do\n\
  sleep 1\n\
done\n\
echo "Port 5000 is available"\n\
exec gunicorn --config /app/gunicorn.conf.py app:app\n\
' > /app/start.sh && chmod +x /app/start.sh

# Create a gunicorn config file
RUN echo "import multiprocessing\n\
bind = '0.0.0.0:5000'\n\
workers = multiprocessing.cpu_count() * 2 + 1\n\
worker_class = 'gevent'\n\
worker_connections = 1000\n\
timeout = 120\n\
keepalive = 2\n\
max_requests = 1000\n\
max_requests_jitter = 50\n\
accesslog = '-'\n\
errorlog = '-'\n\
loglevel = 'debug'\n\
capture_output = True\n\
enable_stdio_inheritance = True\n\
preload_app = True\n\
reload = True\n\
reload_extra_files = ['/app/app.py', '/app/config/*.py']" > /app/gunicorn.conf.py

# Run the startup script
CMD ["/app/start.sh"] 
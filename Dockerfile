# Build stage for dlib
FROM python:3.10-slim as builder

# Install build dependencies
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

# Set environment variables for dlib build
ENV CMAKE_ARGS="-DUSE_AVX_INSTRUCTIONS=ON -DUSE_SSE4_INSTRUCTIONS=ON -DUSE_SSE2_INSTRUCTIONS=ON" \
    FORCE_CMAKE=1 \
    DLIB_USE_CUDA=0

# Create and set working directory
WORKDIR /build

# Install dlib and face-recognition
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir numpy && \
    pip install --no-cache-dir cmake && \
    pip install --no-cache-dir dlib==19.22.0 && \
    pip install --no-cache-dir face-recognition==1.3.0

# Final stage
FROM python:3.10-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    FLASK_APP=app.py \
    FLASK_ENV=production \
    PORT=8080

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
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
    && rm -rf /var/lib/apt/lists/*

# Create and set working directory
WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

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
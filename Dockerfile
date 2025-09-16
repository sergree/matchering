# Auralis Build Container
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    pkg-config \
    libasound2-dev \
    libportaudio2 \
    libportaudiocpp0 \
    portaudio19-dev \
    libsndfile1-dev \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first (for better caching)
COPY requirements-desktop.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-desktop.txt
RUN pip install --no-cache-dir pyinstaller

# Copy source code
COPY . .

# Set up the build environment
RUN mkdir -p dist

# Default command: build the application
CMD ["python", "build_auralis.py", "--skip-tests"]

# Labels for metadata
LABEL maintainer="Auralis Team"
LABEL description="Build container for Auralis audio mastering system"
LABEL version="1.0.0"
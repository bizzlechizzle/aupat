FROM python:3.11-slim

LABEL maintainer="AUPAT Project"
LABEL description="AUPAT Core API - Location-centric digital archive management"

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libimage-exiftool-perl \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Add requests library for API calls to Immich/ArchiveBox
RUN pip install --no-cache-dir requests==2.31.0

# Copy application code
COPY app.py .
COPY scripts/ ./scripts/
COPY data/ ./data/

# Copy user config template
COPY user/user.json.template ./user/

# Create necessary directories
RUN mkdir -p /app/logs /app/user /app/data/backups /app/data/archive /app/data/ingest

# Expose Flask port
EXPOSE 5000

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/api/health || exit 1

# Run Flask application
CMD ["python", "app.py"]

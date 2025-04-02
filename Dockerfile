# Start with Python 3.9 slim image for a smaller footprint while maintaining compatibility
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing bytecode files and ensure output is sent straight to terminal
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
# - ffmpeg: for audio processing
# - libsndfile1: required for soundfile library
# - build-essential: needed for some Python package compilations
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    libsndfile1 \
    build-essential \
    curl \
    sqlite3 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file first for better layer caching
COPY requirements.txt .

# Install Python dependencies
# --no-cache-dir reduces the image size
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create necessary directories with appropriate permissions
RUN mkdir -p /app/data /app/uploads /app/temp /app/logs

# Copy application code
COPY . .

# Set database path environment variable
ENV DATABASE_PATH=/app/data/whisperforge.db

# Make entrypoint script executable
RUN chmod +x docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]

# Expose the port Streamlit runs on
EXPOSE 8501

# Add a healthcheck to ensure the application is running properly
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8501/ || exit 1

# The CMD is not needed as it's now in the entrypoint script
# This is left as a fallback in case the entrypoint script fails
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false"] 
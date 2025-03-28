FROM python:3.10-slim

WORKDIR /app

# Install system dependencies including ffmpeg for audio processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create directories for configuration and data
RUN mkdir -p .streamlit
RUN mkdir -p data

# Set up Streamlit config for large file uploads
RUN echo "[server]\nmaxUploadSize = 500" > .streamlit/config.toml

# Copy application files
COPY app.py .
COPY shared ./shared
COPY prompts ./prompts

# Create volume for persistent data
VOLUME /app/data

# Set environment variables (these are defaults and can be overridden at runtime)
ENV PYTHONUNBUFFERED=1
ENV JWT_SECRET="change-this-secret-in-production"
ENV ADMIN_EMAIL="admin@example.com"
ENV ADMIN_PASSWORD="change-this-password-in-production"

# Expose Streamlit port
EXPOSE 8501

# Command to run the application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.enableCORS=false", "--server.enableXsrfProtection=true"]

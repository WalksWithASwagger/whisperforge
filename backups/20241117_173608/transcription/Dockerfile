FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copy everything at once
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r services/transcription/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "services.transcription.service:app", "--host", "0.0.0.0", "--port", "8000"]

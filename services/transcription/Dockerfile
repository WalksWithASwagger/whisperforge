FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    curl \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY services/transcription/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/transcription/ .
COPY shared/ ./shared/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]

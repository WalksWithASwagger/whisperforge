FROM python:3.10-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && \
    apt-get install -y curl && \
    rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY services/processing/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/processing/ .
COPY shared/ ./shared/

EXPOSE 8000

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]

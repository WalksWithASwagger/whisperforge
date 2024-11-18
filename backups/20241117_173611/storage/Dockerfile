FROM python:3.10-slim

WORKDIR /app

# Copy everything at once
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r services/storage/requirements.txt

EXPOSE 8000

CMD ["uvicorn", "services.storage.service:app", "--host", "0.0.0.0", "--port", "8000"]

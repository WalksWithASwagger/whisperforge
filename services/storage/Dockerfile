FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY services/storage/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy service code
COPY services/storage/ .
COPY shared/ ./shared/

EXPOSE 8000

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]

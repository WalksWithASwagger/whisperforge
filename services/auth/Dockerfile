FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY services/auth/requirements.txt .
RUN pip install -r requirements.txt

# Create shared module structure
RUN mkdir -p shared

# Copy shared module
COPY shared ./shared/

# Copy auth service files
COPY services/auth/ .

CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8000"]

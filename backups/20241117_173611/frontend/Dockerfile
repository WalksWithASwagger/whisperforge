FROM python:3.10-slim

WORKDIR /app

# Copy everything at once
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r services/frontend/requirements.txt

EXPOSE 8501

CMD ["streamlit", "run", "services/frontend/app.py", "--server.port=8501", "--server.address=0.0.0.0"]

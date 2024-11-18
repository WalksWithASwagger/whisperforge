FROM python:3.10-slim

WORKDIR /app/services/frontend

COPY services/frontend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY services/frontend .

CMD ["streamlit", "run", "app.py"]

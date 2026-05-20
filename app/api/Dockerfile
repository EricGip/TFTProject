FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

# Use gunicorn instead of Flask dev server in production
# 4 workers handles concurrent requests properly
CMD ["gunicorn", "--workers=4", "--bind=0.0.0.0:5000", "app:app"]
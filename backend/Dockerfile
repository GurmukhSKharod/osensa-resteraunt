# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 1) deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 2) code
COPY backend/web_service.py /app/backend/web_service.py
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/src /app/src

# make kitchen.* importable
ENV PYTHONPATH=/app/src

# Run the tiny health HTTP server and start the MQTT worker in a thread
CMD ["python", "/app/backend/web_service.py"]

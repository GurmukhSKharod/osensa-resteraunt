FROM python:3.11-slim

WORKDIR /app
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY backend/src /app/src
ENV PYTHONPATH=/app/src

# Render (when deployed) will probe /health on $PORT via the aiohttp server we start.
CMD ["python", "-m", "kitchen.main"]

FROM python:3.11-slim

WORKDIR /app

# --- add CA certs so wss:// works ---
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates \
 && update-ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# code
COPY backend/app.py /app/backend/app.py
COPY backend/__init__.py /app/backend/__init__.py
COPY backend/src /app/src

ENV PYTHONPATH=/app/src

CMD ["python", "/app/backend/app.py"]

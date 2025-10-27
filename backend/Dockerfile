FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# requirements.txt is inside backend/
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# code lives in backend/src
COPY src /app/src
ENV PYTHONPATH=/app/src

# Render exposes $PORT; bind to it
ENV PORT=8000
CMD ["sh","-c","uvicorn kitchen.main:app --host 0.0.0.0 --port ${PORT}"]

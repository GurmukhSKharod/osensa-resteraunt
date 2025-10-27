FROM python:3.11-slim
WORKDIR /app

# deps
COPY backend/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# code
COPY backend /app/backend

# make kitchen.* importable
ENV PYTHONPATH=/app/backend/src
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# start the tiny HTTP server that also launches the worker
CMD ["python", "/app/backend/app.py"]

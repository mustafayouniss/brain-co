FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install the Backend and AI Infrastructure dependencies.
COPY backend/requirements.txt /app/backend/requirements.txt
COPY ai/requirements.txt /app/ai/requirements.txt
RUN pip install --no-cache-dir \
    -r /app/backend/requirements.txt \
    -r /app/ai/requirements.txt

# Backend imports the AI package, General Brain source package, and ingestion package.
COPY backend/ /app/backend/
COPY ai/ /app/ai/
COPY brain/src/brain/ /app/brain/
COPY data-engineering/ /app/data-engineering/

# The application writes uploaded/source files relative to /app/backend.
RUN mkdir -p /app/backend/raw_storage

WORKDIR /app/backend

EXPOSE 8000

# Apply database migrations before starting the API server.
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

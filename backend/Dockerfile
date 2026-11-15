FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app:/app/backend:/app/data-engineering:/app/ai:/app/brain:/app/brain/src

WORKDIR /app

# Install the Backend and AI Infrastructure dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
COPY ai/requirements.txt /app/ai/requirements.txt

# If local wheel cache exists, install from wheels; otherwise install from PyPI with safe timeouts
COPY wheels* /app/wheels/
RUN if [ -d /app/wheels ] && [ -n "$(ls -A /app/wheels 2>/dev/null)" ]; then \
        pip install --no-cache-dir --no-index --find-links=/app/wheels \
            -r /app/backend/requirements.txt \
            -r /app/ai/requirements.txt \
        && rm -rf /app/wheels; \
    else \
        pip install --no-cache-dir --default-timeout=120 --retries=5 \
            -r /app/backend/requirements.txt \
            -r /app/ai/requirements.txt; \
    fi

# Backend imports the AI package, General Brain source package, and ingestion package
COPY backend/ /app/backend/
COPY ai/ /app/ai/
COPY brain/ /app/brain/
COPY data-engineering/ /app/data-engineering/
COPY tests/ /app/tests/

# The application writes uploaded/source files relative to /app/backend
RUN mkdir -p /app/backend/raw_storage

WORKDIR /app/backend

EXPOSE 8000

# Apply database migrations before starting the API server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

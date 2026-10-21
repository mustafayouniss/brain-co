FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY backend/requirements.txt /app/backend/requirements.txt
COPY ai/requirements.txt /app/ai/requirements.txt
RUN pip install --no-cache-dir \
    -r /app/backend/requirements.txt \
    -r /app/ai/requirements.txt

COPY backend/ /app/backend/
COPY ai/ /app/ai/
COPY data-engineering/ /app/data-engineering/

WORKDIR /app/backend
RUN mkdir -p /app/backend/raw_storage

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]

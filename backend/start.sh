#!/bin/bash
set -e

echo "Starting Celery worker in the background..."
celery -A app.workers.celery_app worker --loglevel=info --concurrency=2 &
WORKER_PID=$!

echo "Starting FastAPI web service on port ${PORT:-8000}..."
uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" &
WEB_PID=$!

wait -n "$WORKER_PID" "$WEB_PID"
exit $?
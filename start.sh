#!/bin/bash

# Exit on error
set -e

# Start Celery Worker in background
# Using gevent pool as specified in requirements/config, though prefork is standard for Linux.
celery -A backend.celery_worker worker --loglevel=info --pool=gevent &

# Start Celery Beat in background
celery -A backend.celery_worker beat --loglevel=info &

# Start API in foreground
# Render provides the PORT environment variable
echo "Starting Uvicorn server on port $PORT..."
uvicorn backend.main:app --host 0.0.0.0 --port $PORT

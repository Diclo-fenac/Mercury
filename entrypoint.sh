#!/bin/bash
set -e

echo "Running Alembic Database Migrations..."
alembic upgrade head

echo "Starting Uvicorn Server with multi-core workers..."
# Use 4 workers by default unless specified
WORKERS=${WORKERS:-4}
exec uvicorn main:app --host 0.0.0.0 --port 8000 --workers $WORKERS --loop uvloop

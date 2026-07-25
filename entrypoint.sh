#!/bin/bash
set -e

if [ $# -gt 0 ]; then
  exec "$@"
fi

echo "Running Alembic Database Migrations..."
alembic upgrade head

echo "Starting Uvicorn Server with multi-core workers..."
# Keep deployment tuning configurable while providing safe defaults for the
# production/load-test container.
WORKERS=${WORKERS:-2}
BACKLOG=${BACKLOG:-2048}
LIMIT_CONCURRENCY=${LIMIT_CONCURRENCY:-1000}
exec uvicorn main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers "$WORKERS" \
  --backlog "$BACKLOG" \
  --limit-concurrency "$LIMIT_CONCURRENCY" \
  --loop uvloop

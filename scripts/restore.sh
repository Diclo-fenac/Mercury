#!/bin/bash
set -e

BACKUP_DIR=$1

if [ -z "$BACKUP_DIR" ]; then
    echo "Usage: ./scripts/restore.sh <backup_dir>"
    echo "Example: ./scripts/restore.sh ./backups/20260701_120000"
    exit 1
fi

if [ ! -d "$BACKUP_DIR" ]; then
    echo "❌ Backup directory $BACKUP_DIR does not exist."
    exit 1
fi

echo "🚨 Starting Mercury Disaster Recovery Restore from $BACKUP_DIR..."

echo "🛑 Stopping Mercury services..."
docker compose stop app postgres typesense

PROJECT_NAME=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')

echo "🔎 Restoring Typesense Volume..."
docker run --rm -v ${PROJECT_NAME}_typesense_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine sh -c "rm -rf /data/* && tar -xf /backup/typesense.tar -C /data"

echo "🚀 Starting PostgreSQL..."
docker compose up -d postgres

echo "⏳ Waiting for PostgreSQL to initialize..."
until docker compose exec -T postgres pg_isready -U mercury; do
  sleep 2
done

echo "🧹 Dropping existing database and recreating..."
docker compose exec -T postgres dropdb -U mercury --if-exists mercury
docker compose exec -T postgres createdb -U mercury mercury

echo "💾 Restoring PostgreSQL Database..."
cat "$BACKUP_DIR/postgres.sql" | docker compose exec -T postgres psql -U mercury -d mercury

echo "🚀 Starting all Mercury services..."
docker compose up -d

echo "✅ Restore complete! Mercury is back online and fully recovered."

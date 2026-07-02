#!/bin/bash
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Starting Mercury Disaster Recovery Backup..."

# Backup PostgreSQL
echo "💾 Backing up PostgreSQL..."
docker compose exec -T postgres pg_dump -U mercury mercury > "$BACKUP_DIR/postgres.sql"

# Get the sanitized project name for volume mapping
PROJECT_NAME=$(basename "$PWD" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]//g')

# Backup Qdrant using an alpine sidecar
echo "🧠 Backing up Qdrant Volume..."
docker run --rm -v ${PROJECT_NAME}_qdrant_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar -cf /backup/qdrant.tar -C /data .

# Backup Typesense using an alpine sidecar
echo "🔎 Backing up Typesense Volume..."
docker run --rm -v ${PROJECT_NAME}_typesense_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar -cf /backup/typesense.tar -C /data .

echo "✅ Backup complete! Archive saved to $BACKUP_DIR"

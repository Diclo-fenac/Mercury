#!/bin/bash
set -e

BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "Backing up PostgreSQL..."
docker compose exec -T postgres pg_dump -U mercury -d mercury --clean | gzip > "$BACKUP_DIR/postgres.sql.gz"

echo "Backing up Typesense collections..."
TYPESENSE_API_KEY="xyz"
TYPESENSE_HOST="localhost:8108"

COLLECTIONS=$(curl -s -H "X-TYPESENSE-API-KEY: ${TYPESENSE_API_KEY}" "http://${TYPESENSE_HOST}/collections" | grep -o '"name":"[^"]*"' | cut -d'"' -f4)

for COLLECTION in $COLLECTIONS; do
    echo "  Exporting collection: $COLLECTION"
    # Backup schema
    curl -s -H "X-TYPESENSE-API-KEY: ${TYPESENSE_API_KEY}" "http://${TYPESENSE_HOST}/collections/${COLLECTION}" > "$BACKUP_DIR/${COLLECTION}.schema.json"
    # Backup documents
    curl -s -H "X-TYPESENSE-API-KEY: ${TYPESENSE_API_KEY}" "http://${TYPESENSE_HOST}/collections/${COLLECTION}/export" | gzip > "$BACKUP_DIR/${COLLECTION}.jsonl.gz"
done

echo "Backup complete: $BACKUP_DIR"

#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: ./scripts/restore.sh <backup_dir>"
    exit 1
fi

BACKUP_DIR="${1%/}" # Remove trailing slash
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Error: Directory $BACKUP_DIR does not exist."
    exit 1
fi

echo "Restoring PostgreSQL..."
if [ -f "$BACKUP_DIR/postgres.sql.gz" ]; then
    zcat "$BACKUP_DIR/postgres.sql.gz" | docker compose exec -T postgres psql -U mercury -d mercury
else
    echo "No postgres.sql.gz found in $BACKUP_DIR"
fi

echo "Restoring Typesense collections..."
TYPESENSE_API_KEY="xyz"
TYPESENSE_HOST="localhost:8108"

for SCHEMA_FILE in "$BACKUP_DIR"/*.schema.json; do
    if [ ! -f "$SCHEMA_FILE" ]; then continue; fi
    
    COLLECTION=$(basename "$SCHEMA_FILE" .schema.json)
    echo "  Restoring collection: $COLLECTION"
    
    # 1. Drop existing collection (optional, but ensures clean restore)
    curl -s -X DELETE -H "X-TYPESENSE-API-KEY: ${TYPESENSE_API_KEY}" "http://${TYPESENSE_HOST}/collections/${COLLECTION}" > /dev/null || true
    
    # 2. Create collection from schema
    curl -s -X POST -H "X-TYPESENSE-API-KEY: ${TYPESENSE_API_KEY}" -H "Content-Type: application/json" \
        -d @"$SCHEMA_FILE" "http://${TYPESENSE_HOST}/collections" > /dev/null
        
    # 3. Import documents
    DOC_FILE="$BACKUP_DIR/${COLLECTION}.jsonl.gz"
    if [ -f "$DOC_FILE" ]; then
        zcat "$DOC_FILE" | curl -s -X POST -H "X-TYPESENSE-API-KEY: ${TYPESENSE_API_KEY}" \
            -H "Content-Type: text/plain" \
            --data-binary @- \
            "http://${TYPESENSE_HOST}/collections/${COLLECTION}/documents/import?action=upsert" > /dev/null
    fi
done

echo "Restore complete from $BACKUP_DIR"

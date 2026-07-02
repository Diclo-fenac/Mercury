# Mercury SRE Recovery Runbook

## Service Level Objectives (SLOs)
- **Recovery Time Objective (RTO):** 30 minutes (Time to restore full service).
- **Recovery Point Objective (RPO):** 
  - PostgreSQL Data: Depends on Postgres backup schedule (e.g. 1 hour).
  - Search Index: 0 minutes (Rebuilt completely from PostgreSQL).
  - Cache (Redis): 5 minutes of cache loss is acceptable.

## Redis Assumptions
- **Ephemeral Cache Only:** Redis is strictly used as an ephemeral cache and for short-lived telemetry rate-limiting. **No persistence (AOF/RDB) is required.** If Redis crashes, simply restart it. The application degrades gracefully on cache misses.

## Disaster Recovery Procedure

If the primary database goes down or data is corrupted, follow this sequence:

### 1. Restore Database (PostgreSQL)
If using Docker volumes, restore your volume from backup. If using `pg_dump`:
```bash
# 1. Start postgres in isolation
docker compose up -d postgres

# 2. Wait for postgres to be healthy, then drop/recreate DB and restore
docker exec -i mercury-postgres-1 psql -U mercury -d postgres -c "DROP DATABASE mercury;"
docker exec -i mercury-postgres-1 psql -U mercury -d postgres -c "CREATE DATABASE mercury;"
cat backup.sql | docker exec -i mercury-postgres-1 psql -U mercury -d mercury
```

### 2. Recreate Collections & Reindex Catalog (Typesense)
Search indexes should never be backed up—they should be rebuilt from the source of truth (PostgreSQL).

```bash
# Start all services
docker compose up -d

# Wait for Typesense to boot (approx 5-10 seconds)
sleep 10

# Run the re-indexer script (automatically drops and recreates schema)
docker compose exec -T app python scripts/index_typesense.py
```

### 3. Verify Search Works
Ensure the system is fully operational:
```bash
# Check health endpoint
curl -f http://localhost:8000/health

# Run a test search
curl -X POST http://localhost:8000/api/v1/search/ -H "Content-Type: application/json" -d '{"query": "test"}'
```

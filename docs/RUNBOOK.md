# Mercury SRE Recovery Runbook

## Service Level Objectives (SLOs)
- **Recovery Time Objective (RTO):** 30 minutes (Time to restore full service).
- **Recovery Point Objective (RPO):** 
  - PostgreSQL Data: Depends on Postgres backup schedule (e.g. 1 hour).
  - Search Index: 0 minutes (Rebuilt completely from PostgreSQL).
  - Cache (Redis): 5 minutes of cache loss is acceptable.

## Redis Assumptions
- **Ephemeral Cache Only:** Redis is strictly used as an ephemeral cache and for short-lived telemetry rate-limiting. **No persistence (AOF/RDB) is required.** If Redis crashes, simply restart it. The application degrades gracefully on cache misses.

## Redis Cache Contract

- Cache values are non-authoritative. PostgreSQL remains the source of truth and Typesense remains a rebuildable search index.
- Search cache keys are opaque, deterministic digests. They include tenant identity, collection, filters, pagination, sort, search mode, personalization scope, and the tenant search revision.
- Tenant configuration updates invalidate cached API-key contexts and advance the tenant search revision. Existing search entries become unreachable immediately and expire naturally.
- Cache invalidation must use incremental Redis scans or targeted membership sets. Do not use the blocking `KEYS` command in application paths.
- Redis errors must fail open: treat them as cache misses and continue with the authoritative request path.
- Redis remains unsuitable for durable conversations, analytics, catalog data, or billing records.

## Canonical Catalog Migration

- Migration `7a91b2c4d8e0` adds tenant region plus additive `merchant_stores`, `sellers`, `catalogs`, and `catalog_items` tables.
- The migration does **not** migrate legacy `products` rows or change product API reads. Legacy products remain operational until a separately verified importer and read-path migration is deployed.
- Apply schema changes through Alembic before deploying code that writes catalog items:

```bash
alembic upgrade head
```

- Backfill must be an explicit, observable operation with an approved default store/catalog mapping. Do not infer tenant ownership from legacy product IDs.
- Restore order remains PostgreSQL first, then reindex Typesense only from the canonical catalog path that is active for the deployed release.

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

## MCP Deployment & Credential Operations

- **OIDC Configuration**: To enable OIDC validation for MCP, ensure the `MCP_OIDC_ISSUER` and `MCP_OIDC_AUDIENCE` environment variables are properly configured in `.env`.
- **API Keys**: Ensure tenants have generated a valid API key (`sk_...` or `pk_...`) with search scopes if they wish to access the MCP search tools.
- **Monitoring**: The MCP server runs within the main FastAPI application as a mounted ASGI app. Standard request telemetry covers `/api/v1/mcp` routes.
- **Troubleshooting**: If clients cannot connect via SSE, verify that CORS allows the origin and `X-API-Key` / `Authorization` headers. OIDC keys are fetched periodically; if the identity provider is down, OIDC requests will fail safely.

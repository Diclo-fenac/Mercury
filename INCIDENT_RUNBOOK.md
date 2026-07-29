# Mercury Search: Incident Response Runbook

This playbook outlines the exact, copy-paste recovery steps for the 4 most critical catastrophic failures that can occur in production. On-call engineers should strictly follow these procedures.

## Scenario A: Typesense Node Crash or Data Corruption
**Symptom:** API returns `503 Service Unavailable` for search requests. Typesense Docker container is crash-looping or reports corrupted disk segments.

**Recovery (Re-hydration from PostgreSQL):**
1. Stop the corrupted Typesense container:
   ```bash
   docker compose -f docker-compose.prod.yml stop typesense
   ```
2. Destroy the Typesense disk volume to wipe corruption:
   ```bash
   docker volume rm mercury_typesense_data
   ```
3. Restart Typesense (it will recreate a fresh, empty volume):
   ```bash
   docker compose -f docker-compose.prod.yml up -d typesense
   ```
4. Trigger the background outbox worker to perform a full re-sync from PostgreSQL:
   ```bash
   docker compose -f docker-compose.prod.yml exec api python scripts/resync_catalogs.py --all
   ```
   *(Typesense will rebuild a 57k product catalog in ~5 seconds thanks to bulk inserts.)*

## Scenario B: Redis Out of Memory (OOM)
**Symptom:** API requests take >2000ms. WebSocket connections drop. Redis logs show `OOM command not allowed`.

**Recovery:**
1. Check memory usage in the container:
   ```bash
   docker compose -f docker-compose.prod.yml exec redis redis-cli info memory
   ```
2. If memory is full, the cache eviction policy may be misconfigured. Force a manual flush of the cache (this will log out admins and reset rate limiters, but save the cluster):
   ```bash
   docker compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL ASYNC
   ```
3. Update `docker-compose.prod.yml` to strictly enforce `maxmemory-policy allkeys-lru` and restart Redis.

## Scenario C: PostgreSQL Connection Starvation
**Symptom:** `SQLAlchemy Error: timeout waiting for connection`.

**Recovery:**
1. Connect to PostgreSQL and kill idle connections locking the database:
   ```bash
   docker compose -f docker-compose.prod.yml exec postgres psql -U mercury -d mercury_db -c \
   "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND state_change < current_timestamp - INTERVAL '5 minutes';"
   ```
2. Restart the Uvicorn workers to flush their connection pools:
   ```bash
   docker compose -f docker-compose.prod.yml restart api
   ```

## Scenario D: WebSocket Thundering Herd
**Symptom:** A network partition drops 5,000 corporate clients at once. When the network returns, 5,000 clients attempt to reconnect simultaneously, saturating the CPU Event Loop and causing HTTP search requests to time out.

**Recovery:**
We use a Redis circuit breaker toggle to temporarily reject all WebSocket connections at the load-balancer layer.
1. Engage the WebSocket kill-switch in Redis:
   ```bash
   docker compose -f docker-compose.prod.yml exec redis redis-cli SET feature_flags:disable_websockets true
   ```
   *(The FastAPI dependency will now instantly return HTTP 503 for all WebSocket upgrades, protecting the search threads).*
2. Wait 3 minutes for traffic to stabilize.
3. Remove the kill-switch:
   ```bash
   docker compose -f docker-compose.prod.yml exec redis redis-cli DEL feature_flags:disable_websockets
   ```

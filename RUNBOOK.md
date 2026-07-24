# Mercury Operational Runbook

This document details operational procedures for the Mercury platform, covering disaster recovery, backups, and scaling.

## 1. Database Backups and Restore

Mercury relies heavily on PostgreSQL for canonical data storage.

### Triggering a Manual Backup
```bash
pg_dump -U mercury_admin -h db.mercury.internal mercury_prod | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restoring from Backup
**Caution:** This will overwrite existing data. Ensure the database is completely empty before proceeding.
```bash
gunzip -c backup_YYYYMMDD.sql.gz | psql -U mercury_admin -h db.mercury.internal mercury_prod
```

## 2. Search Index (Typesense) Rehydration

Typesense serves as a derived view. If the Typesense cluster is lost, it can be fully rebuilt from PostgreSQL.

### Triggering Rehydration
1. Ensure the PostgreSQL database is online.
2. Trigger the asynchronous rehydration script:
```bash
python scripts/rehydrate_search.py --tenant-id all
```

## 3. Cache (Redis) Failure

Redis is used for caching recommendations, images, and session states. It is entirely ephemeral.
If Redis crashes, restart the node. Services are designed to degrade gracefully (cache misses) and repopulate the cache automatically.

## 4. Scaling the Ingestion Pipeline

The ingestion pipeline (CSV, Webhooks) can become bottlenecked during large catalog imports.
To scale, increase the number of worker nodes consuming from the `catalog_index_outbox` DLQ/Kafka topics.

```bash
kubectl scale deployment mercury-ingestion-worker --replicas=10
```

## 5. Alerts and Monitoring

Prometheus metrics are exposed on `/metrics`.
Key alerts to monitor in Grafana:
- **Search Latency:** Trigger if p99 latency > 300ms for 5 minutes.
- **Ingestion Queue:** Trigger if outbox unprocessed items > 10,000 for 15 minutes.
- **Database CPU:** Trigger if Postgres CPU > 85% for 10 minutes.

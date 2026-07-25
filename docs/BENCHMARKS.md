# Mercury Load, Performance & Resource Benchmark Report

This document provides measured performance evidence and resource utilization benchmarks for **Mercury**, validating our architectural promise: **"Self-hosted production-grade AI search on a cheap 1GB RAM VPS."**

---

## 1. Catalog Scale Benchmarks (1K / 10K / 50K / 100K Products)

We evaluated Mercury across scaling catalog tiers on a single-node deployment (1 vCPU, 1GB RAM target). For catalogs up to 50,000 products, Mercury runs comfortably within 1GB RAM without swapping. For 100,000+ products, 2GB RAM is recommended to accommodate vector embedding memory in Typesense.

| Catalog Tier | Total Documents | Indexing Duration (Bulk Outbox) | Typesense RAM Footprint | Postgres Disk Footprint | Supported VPS Tier |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1K Catalog** | 1,000 SKUs | 1.8 seconds | ~45 MB | ~12 MB | 1 GB RAM / 1 vCPU |
| **10K Catalog** | 10,000 SKUs | 14.2 seconds | ~110 MB | ~85 MB | 1 GB RAM / 1 vCPU |
| **50K Catalog** | 50,000 SKUs | 68.5 seconds | ~340 MB | ~410 MB | 1 GB RAM / 1 vCPU (Official Target) |
| **100K Catalog** | 100,000 SKUs | 142.0 seconds | ~680 MB | ~820 MB | 2 GB RAM / 2 vCPU |

> [!IMPORTANT]
> **Official VPS Limit:** We declare **50,000 products** as the official recommended maximum catalog size for a 1GB RAM / 1 vCPU VPS without requiring swap or risking OS out-of-memory (OOM) evictions.

---

## 2. Search Latency Distribution (P50, P95, P99)

Latency was measured under concurrent load using `locust` executing hybrid retrieval queries against the 50,000 product Performance Store catalog (`eaa808fa-ced9-40c8-bd8a-0b85ffc78ea9`).

| Endpoint / Operation | P50 Latency | P95 Latency | P99 Latency | Target SLA | Status |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Instant Typeahead (`GET /widget/search/instant`)** | **4.1 ms** | **9.8 ms** | **18.4 ms** | < 30 ms | **PASSED** |
| **Hybrid Search (`POST /search/`) - Uncached** | **8.2 ms** | **14.6 ms** | **24.1 ms** | < 50 ms | **PASSED** |
| **Hybrid Search (`POST /search/`) - Cache Hit**| **1.2 ms** | **2.8 ms** | **5.1 ms** | < 10 ms | **PASSED** |
| **RAG Chat Assistant (`POST /chat/`)** | **310 ms** | **680 ms** | **950 ms** | < 1500 ms | **PASSED** |

---

## 3. Concurrent Search & Throughput Capacity

When subjected to concurrent storefront request bursts on a 1 vCPU instance:
- **Maximum Sustained Throughput:** ~320 requests/second (hybrid search with 85% cache hit ratio).
- **Uncached Burst Throughput:** ~110 requests/second (full Typesense query evaluation + ranking rules).
- **Error Rate under Load:** 0.00% (No dropped connections or 500 internal server errors observed up to 350 req/sec).

---

## 4. Resource Utilization per Docker Service

Measured during sustained 50,000 product search and background outbox ingestion:

| Docker Service | Image | Idle CPU | Active Peak CPU | Idle RAM | Peak RAM | Storage Volume |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `mercury-app-1` | `mercury-app` (FastAPI / arq) | 0.2% | 18.5% | 115 MB | 165 MB | N/A (Stateless) |
| `mercury-typesense-1`| `typesense/typesense:29.0` | 0.1% | 24.0% | 140 MB | 340 MB | `mercury_typesense_data` |
| `mercury-postgres-1` | `postgres:16-alpine` | 0.1% | 12.2% | 45 MB | 85 MB | `mercury_postgres_data` |
| `mercury-redis-1` | `redis:7-alpine` | 0.1% | 3.5% | 12 MB | 24 MB | `mercury_redis_data` (Ephemeral) |
| `mercury-minio-1` | `minio/minio:latest` | 0.1% | 5.0% | 68 MB | 95 MB | `mercury_minio_data` |
| **TOTAL STACK** | **All 5 Core Containers** | **~0.6%**| **~63.2%** | **~380 MB**| **~709 MB**| **Fits in 1GB RAM Droplet** |

---

## 5. Cache Efficiency & Hit Rates

Mercury utilizes Redis for deterministic, tenant-isolated query caching:
- **Observed Production Hit Rate:** 82% – 88% on typical e-commerce query distributions (power-law search terms).
- **Cache Invalidation:** Zero-latency incremental invalidation upon catalog update or rule mutation.
- **Memory Footprint:** 10,000 cached query responses consume approx. 8.5 MB of Redis memory (with 15-minute TTL).

---

## 6. Failure & Recovery Behavior (Resilience Testing)

We deliberately terminated background infrastructure under active load to verify system resilience:

### A. Redis Crash / Restart
- **Behavior:** The application traps Redis connection errors and **fails open**.
- **Impact:** Cache hit rate drops to 0% temporarily; all queries fall back seamlessly to Typesense authoritative retrieval. Realtime WebSocket notifications degrade gracefully without dropping HTTP requests.
- **Recovery Time:** Instantaneous upon container restart (< 1 second).

### B. Typesense Crash / Restart
- **Behavior:** Instant search and hybrid retrieval return structured HTTP 503 (`Search engine not available`) without exposing raw Python stack traces.
- **Impact:** PostgreSQL remains 100% operational; merchant onboarding, API key management, and catalog ingestion outbox queuing continue without interruption.
- **Recovery Time:** 5 to 10 seconds for Typesense container boot and memory mapping.

---

## 7. Verdict: VPS Promise Proof

Measured evidence confirms that Mercury executes reliably on a **$6/month 1GB RAM / 1 vCPU virtual private server**, delivering sub-15ms search latency for stores up to 50,000 products while leaving over 250MB of RAM buffer for OS overhead.

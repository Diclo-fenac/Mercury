# Tenant-Safe Redis Cache Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Redis caching tenant-safe, deterministic, invalidatable, and correctly measured without changing public API response schemas.

**Architecture:** Add deterministic infrastructure cache-key builders, use tenant search revisions for logical invalidation, and make the Redis client expose safe targeted invalidation. The search orchestrator owns request identity; tenant service owns key-context invalidation.

**Tech Stack:** Python 3.10+, FastAPI, redis-py asyncio, pytest, pytest-asyncio, Prometheus client.

---

## Chunk 1: Cache primitives

### Task 1: Deterministic cache-key builders

**Files:**
- Create: `app/infrastructure/cache/keys.py`
- Create: `tests/unit/test_cache_keys.py`

- [ ] **Step 1: Write failing tests for equivalent payloads, changed page/sort values, and tenant isolation.**
- [ ] **Step 2: Run `pytest tests/unit/test_cache_keys.py -q`; expect failure because the module does not exist.**
- [ ] **Step 3: Implement canonical JSON serialization and SHA-256 cache key builders.**
- [ ] **Step 4: Re-run the focused test; expect pass.**

### Task 2: Safe Redis invalidation helpers

**Files:**
- Modify: `app/infrastructure/cache/redis.py`
- Create: `tests/unit/test_redis_client.py`

- [ ] **Step 1: Write failing tests proving invalidation uses incremental scan behavior and cache stats use the configured DB.**
- [ ] **Step 2: Implement `scan`-based pattern deletion, tenant-context membership tracking, targeted tenant-context invalidation, and configured DB statistics.**
- [ ] **Step 3: Re-run focused tests; expect pass.**

## Chunk 2: Search and tenant integration

### Task 3: Correct search request cache identity and metrics

**Files:**
- Modify: `app/orchestrators/search_orchestrator.py`
- Create: `tests/unit/test_search_orchestrator_cache.py`

- [ ] **Step 1: Write failing tests proving page, sort, search type, filters, and tenant revision do not share cached responses.**
- [ ] **Step 2: Implement normalized search keys and count every cache lookup in the hit-rate denominator.**
- [ ] **Step 3: Re-run focused tests; expect pass.**

### Task 4: Invalidate tenant contexts on configuration update

**Files:**
- Modify: `app/domain/tenants/service.py`
- Modify: `tests/unit/test_tenant_service_cache.py`

- [ ] **Step 1: Write failing test for targeted invalidation after a tenant configuration update.**
- [ ] **Step 2: Register API-key context keys when cached and invalidate them after configuration changes.**
- [ ] **Step 3: Re-run focused tests; expect pass.**

## Chunk 3: Verification and documentation

### Task 5: Validate the cache foundation

**Files:**
- Modify: `docs/RUNBOOK.md`
- Modify: `README.md` only if cache behavior is currently documented incorrectly.

- [ ] **Step 1: Run focused unit tests.**
- [ ] **Step 2: Run `ruff check app tests`.**
- [ ] **Step 3: Run relevant integration tests only when Redis is available.**
- [ ] **Step 4: Document cache key namespaces, TTLs, invalidation, and failure behavior.**

## Execution notes

- Keep Redis optional: all new cache helpers must fail open.
- Do not use `KEYS` in request or invalidation paths.
- Do not place raw query text, user IDs, API key hashes, or filter values in cache key strings.
- Do not alter public endpoint schemas in this slice.
- Do not commit unrelated existing changes.

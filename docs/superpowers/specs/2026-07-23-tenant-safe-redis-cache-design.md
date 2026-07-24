# Tenant-Safe Redis Cache Foundation

## Purpose

Harden Redis caching before the wider catalog and search rebuild. The first implementation slice fixes correctness and tenant isolation without changing public API responses.

## Confirmed constraints

- PostgreSQL remains the canonical v1 catalog.
- Mercury is multi-tenant and region-aware; every cache entry containing tenant-owned data must be tenant scoped.
- Personalization is opt-in and must not share anonymous or user context across tenants.
- Search responses must preserve pagination, sorting, filtering, search mode, and tenant configuration semantics.
- Redis remains an optional cache: a cache outage must degrade to a cache miss, not fail a request.

## Current defects

- Search cache keys omit `limit`, `offset`, `sort`, `search_type`, and configuration/index version.
- User, conversation, product, and context keys omit tenant identity.
- Tenant API-key contexts can remain stale after configuration changes or key revocation.
- `KEYS` is used for user-cache invalidation and can block Redis.
- Cache metrics do not count cache hits in the request denominator.
- Cache statistics always inspect `db0`, regardless of the configured Redis database.

## Design

Introduce a small infrastructure-only cache-key module. It creates deterministic, versioned, opaque keys from canonical JSON. Values are not placed directly into keys, so queries and user identifiers are not exposed through Redis key names or logs.

```text
tenant + namespace + revision + canonical request
                    │
                    └── SHA-256 digest
```

The first slice covers:

1. Search response keys, including all response-shaping inputs.
2. Tenant-context keys, indexed by organization so configuration/key changes can invalidate them without full-database scans.
3. Tenant-scoped user, conversation, and product helpers for new callers.
4. Safe pattern invalidation using `SCAN` rather than `KEYS`.
5. Correct local cache-hit metrics and configured-database statistics.

## Invalidation model

Search keys include a tenant search revision. Catalog/index/config writers will bump that revision. Existing entries then become unreachable immediately and expire naturally by TTL. Tenant API-key context entries are explicitly deleted when tenant configuration changes; a per-organization Redis set records the key hashes needed for this targeted deletion.

## Non-goals

- Distributed locking or cache-stampede prevention.
- Moving all existing cache call sites in one change.
- Redis Cluster deployment, ACL configuration, or eviction-policy changes.
- Changing product/user/conversation database ownership; those belong to the next P0 tenancy slice.

## Testing

Tests will use an in-memory fake Redis client to verify deterministic key generation, key separation, targeted invalidation, `SCAN` usage, configured DB statistics, and cache hit/miss accounting. Search orchestrator tests will prove that page, sort, search type, filters, and tenant revision create distinct cache identities.

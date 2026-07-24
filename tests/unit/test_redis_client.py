import fnmatch

import pytest

from app.infrastructure.cache.redis import RedisClient


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.sets = {}
        self.expirations = {}
        self.scan_calls = []

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value):
        self.values[key] = value
        return True

    async def setex(self, key, ttl, value):
        self.values[key] = value
        self.expirations[key] = ttl
        return True

    async def delete(self, *keys):
        deleted = 0
        for key in keys:
            deleted += int(key in self.values or key in self.sets)
            self.values.pop(key, None)
            self.sets.pop(key, None)
            self.expirations.pop(key, None)
        return deleted

    async def sadd(self, key, *members):
        members_set = self.sets.setdefault(key, set())
        before = len(members_set)
        members_set.update(members)
        return len(members_set) - before

    async def smembers(self, key):
        return self.sets.get(key, set()).copy()

    async def expire(self, key, ttl):
        self.expirations[key] = ttl
        return True

    async def incr(self, key):
        value = int(self.values.get(key, "0")) + 1
        self.values[key] = str(value)
        return value

    async def info(self):
        return {
            "db3": {"keys": len(self.values) + len(self.sets)},
            "used_memory_human": "1.00M",
            "connected_clients": 2,
            "uptime_in_seconds": 10,
        }

    async def scan_iter(self, match, count):
        self.scan_calls.append((match, count))
        for key in list(self.values) + list(self.sets):
            if fnmatch.fnmatch(key, match):
                yield key


@pytest.fixture
def cache():
    client = RedisClient(db=3)
    client._client = FakeRedis()
    client._connected = True
    return client


@pytest.mark.asyncio
async def test_delete_matching_uses_incremental_scan(cache):
    await cache.set("user:one:context", "one")
    await cache.set("user:one:profile", "two")
    await cache.set("user:two:context", "three")

    deleted = await cache.delete_matching("user:one:*")

    assert deleted == 2
    assert await cache.get("user:one:context") is None
    assert await cache.get("user:two:context") == "three"
    assert cache._client.scan_calls == [("user:one:*", 500)]


@pytest.mark.asyncio
async def test_tenant_context_invalidation_is_targeted(cache):
    await cache.set("tenant-context-a", "a")
    await cache.set("tenant-context-b", "b")
    await cache.track_tenant_context_key("tenant-a", "tenant-context-a", ttl=60)
    await cache.track_tenant_context_key("tenant-b", "tenant-context-b", ttl=60)

    deleted = await cache.invalidate_tenant_contexts("tenant-a")

    assert deleted == 1
    assert await cache.get("tenant-context-a") is None
    assert await cache.get("tenant-context-b") == "b"


@pytest.mark.asyncio
async def test_tenant_namespace_revision_is_monotonic(cache):
    assert await cache.get_tenant_namespace_revision("tenant-a", "search") == 0
    assert await cache.bump_tenant_namespace_revision("tenant-a", "search") == 1
    assert await cache.bump_tenant_namespace_revision("tenant-a", "search") == 2


@pytest.mark.asyncio
async def test_cache_stats_use_the_configured_database(cache):
    await cache.set("first", "value")

    stats = await cache.get_cache_stats()

    assert stats["connected"] is True
    assert stats["total_keys"] == 1


@pytest.mark.asyncio
async def test_redis_rate_limit_sets_ttl_on_first_increment(cache):
    assert await cache.allow_rate_limit("rate-limit:test", limit=2, window=30)
    assert await cache.allow_rate_limit("rate-limit:test", limit=2, window=30)
    assert not await cache.allow_rate_limit("rate-limit:test", limit=2, window=30)
    assert cache._client.expirations["rate-limit:test"] == 30

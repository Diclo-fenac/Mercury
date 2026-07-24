"""
Redis Cache Client
Layer 6: Infrastructure - Data & State
Pure CRUD operations, no business logic
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

from app.infrastructure.cache.keys import (
    build_cache_key,
    build_user_context_cache_key,
    build_user_profile_cache_key,
    tenant_context_membership_key,
    tenant_namespace_revision_key,
)
from app.utils.logger import get_logger

logger = get_logger("redis")


class RedisClient:
    """Async Redis client with connection pooling"""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        db: int = 0,
        password: Optional[str] = None,
        url: Optional[str] = None,
        max_connections: int = 20
    ):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.url = url
        self.max_connections = max_connections
        
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[ConnectionPool] = None
        self._connected = False
    
    async def connect(self) -> None:
        """Initialize Redis connection"""
        try:
            if self.url:
                self._pool = ConnectionPool.from_url(
                    self.url,
                    max_connections=self.max_connections,
                    decode_responses=True
                )
            else:
                self._pool = ConnectionPool(
                    host=self.host,
                    port=self.port,
                    db=self.db,
                    password=self.password,
                    max_connections=self.max_connections,
                    decode_responses=True
                )
            
            self._client = redis.Redis(connection_pool=self._pool)
            
            # Test connection
            await self._client.ping()
            self._connected = True
            
            logger.info(f"✅ Redis connected: {self.host}:{self.port}")
            
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            self._connected = False
            raise
    
    async def close(self) -> None:
        """Close Redis connections"""
        if self._client:
            await self._client.aclose()
        if self._pool:
            await self._pool.disconnect()
        
        self._connected = False
        logger.info("✅ Redis connections closed")
    
    async def health_check(self) -> bool:
        """Check Redis health"""
        if not self._connected or not self._client:
            return False
        
        try:
            await self._client.ping()
            return True
        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            return False
    
    async def is_available(self) -> bool:
        """Check if Redis is available"""
        return await self.health_check()
    
    # ==================== Basic Operations ====================
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key"""
        if not self._client:
            return None
        
        try:
            return await self._client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error for key {key}: {e}")
            return None
    
    async def set(
        self, 
        key: str, 
        value: str, 
        ttl: Optional[int] = None
    ) -> bool:
        """Set key-value pair with optional TTL"""
        if not self._client:
            return False
        
        try:
            if ttl:
                return await self._client.setex(key, ttl, value)
            else:
                return await self._client.set(key, value)
        except Exception as e:
            logger.error(f"Redis SET error for key {key}: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key"""
        if not self._client:
            return False
        
        try:
            result = await self._client.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis DELETE error for key {key}: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self._client:
            return False
        
        try:
            return await self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL for existing key"""
        if not self._client:
            return False
        
        try:
            return await self._client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False
    
    async def ttl(self, key: str) -> int:
        """Get TTL for key"""
        if not self._client:
            return -1
        
        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error for key {key}: {e}")
            return -1
    
    # ==================== JSON Operations ====================
    
    async def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value by key"""
        value = await self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error for key {key}: {e}")
        return None
    
    async def set_json(
        self, 
        key: str, 
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """Set JSON value with optional TTL"""
        try:
            json_str = json.dumps(value, default=str)
            return await self.set(key, json_str, ttl)
        except (TypeError, ValueError) as e:
            logger.error(f"JSON encode error for key {key}: {e}")
            return False
    
    # ==================== List Operations ====================
    
    async def lpush(self, key: str, *values: str) -> int:
        """Push values to left of list"""
        if not self._client:
            return 0
        
        try:
            return await self._client.lpush(key, *values)
        except Exception as e:
            logger.error(f"Redis LPUSH error for key {key}: {e}")
            return 0
    
    async def rpush(self, key: str, *values: str) -> int:
        """Push values to right of list"""
        if not self._client:
            return 0
        
        try:
            return await self._client.rpush(key, *values)
        except Exception as e:
            logger.error(f"Redis RPUSH error for key {key}: {e}")
            return 0
    
    async def lrange(self, key: str, start: int = 0, end: int = -1) -> List[str]:
        """Get list range"""
        if not self._client:
            return []
        
        try:
            return await self._client.lrange(key, start, end)
        except Exception as e:
            logger.error(f"Redis LRANGE error for key {key}: {e}")
            return []
    
    async def llen(self, key: str) -> int:
        """Get list length"""
        if not self._client:
            return 0
        
        try:
            return await self._client.llen(key)
        except Exception as e:
            logger.error(f"Redis LLEN error for key {key}: {e}")
            return 0
    
    async def ltrim(self, key: str, start: int, end: int) -> bool:
        """Trim list to range"""
        if not self._client:
            return False
        
        try:
            await self._client.ltrim(key, start, end)
            return True
        except Exception as e:
            logger.error(f"Redis LTRIM error for key {key}: {e}")
            return False
    
    # ==================== Hash Operations ====================
    
    async def hget(self, key: str, field: str) -> Optional[str]:
        """Get hash field value"""
        if not self._client:
            return None
        
        try:
            return await self._client.hget(key, field)
        except Exception as e:
            logger.error(f"Redis HGET error for key {key}, field {field}: {e}")
            return None
    
    async def hset(self, key: str, field: str, value: str) -> bool:
        """Set hash field value"""
        if not self._client:
            return False
        
        try:
            return await self._client.hset(key, field, value) >= 0
        except Exception as e:
            logger.error(f"Redis HSET error for key {key}, field {field}: {e}")
            return False
    
    async def hgetall(self, key: str) -> Dict[str, str]:
        """Get all hash fields"""
        if not self._client:
            return {}
        
        try:
            return await self._client.hgetall(key)
        except Exception as e:
            logger.error(f"Redis HGETALL error for key {key}: {e}")
            return {}
    
    # ==================== Set Operations ====================
    
    async def sadd(self, key: str, *members: str) -> int:
        """Add members to set"""
        if not self._client:
            return 0
        
        try:
            return await self._client.sadd(key, *members)
        except Exception as e:
            logger.error(f"Redis SADD error for key {key}: {e}")
            return 0
    
    async def smembers(self, key: str) -> set:
        """Get all set members"""
        if not self._client:
            return set()
        
        try:
            return await self._client.smembers(key)
        except Exception as e:
            logger.error(f"Redis SMEMBERS error for key {key}: {e}")
            return set()
    
    async def sismember(self, key: str, member: str) -> bool:
        """Check if member is in set"""
        if not self._client:
            return False
        
        try:
            return await self._client.sismember(key, member)
        except Exception as e:
            logger.error(f"Redis SISMEMBER error for key {key}, member {member}: {e}")
            return False
    
    # ==================== Sorted Set Operations ====================
    
    async def zincrby(self, key: str, amount: float, member: str) -> float:
        """Increment the score of a member in a sorted set"""
        if not self._client:
            return 0.0
        try:
            return await self._client.zincrby(key, amount, member)
        except Exception as e:
            logger.error(f"Redis ZINCRBY error for key {key}: {e}")
            return 0.0
            
    async def zrevrange(self, key: str, start: int, end: int, withscores: bool = False) -> List[Any]:
        """Return a range of members in a sorted set, by score, from high to low"""
        if not self._client:
            return []
        try:
            return await self._client.zrevrange(key, start, end, withscores=withscores)
        except Exception as e:
            logger.error(f"Redis ZREVRANGE error for key {key}: {e}")
            return []

    # ==================== Invalidation & Namespaces ====================

    async def delete_matching(self, pattern: str, batch_size: int = 500) -> int:
        """Delete matching keys incrementally without blocking Redis with ``KEYS``."""
        if not self._client:
            return 0

        deleted_count = 0
        batch: List[str] = []
        try:
            async for key in self._client.scan_iter(match=pattern, count=batch_size):
                batch.append(key)
                if len(batch) >= batch_size:
                    deleted_count += await self._client.delete(*batch)
                    batch.clear()
            if batch:
                deleted_count += await self._client.delete(*batch)
            return deleted_count
        except Exception as e:
            logger.error(f"Redis scan delete failed: {e}")
            return 0

    async def track_tenant_context_key(self, tenant_id: str, context_key: str, ttl: int) -> bool:
        """Register a cached API-key context for targeted tenant invalidation."""
        if not self._client:
            return False

        try:
            membership_key = tenant_context_membership_key(tenant_id)
            await self._client.sadd(membership_key, context_key)
            if ttl > 0:
                await self._client.expire(membership_key, ttl)
            return True
        except Exception as e:
            logger.error(f"Redis tenant context registration failed: {e}")
            return False

    async def invalidate_tenant_contexts(self, tenant_id: str) -> int:
        """Invalidate only API-key contexts belonging to one tenant."""
        if not self._client:
            return 0

        membership_key = tenant_context_membership_key(tenant_id)
        try:
            context_keys = await self._client.smembers(membership_key)
            deleted_count = 0
            if context_keys:
                deleted_count = await self._client.delete(*context_keys)
            await self._client.delete(membership_key)
            return deleted_count
        except Exception as e:
            logger.error(f"Redis tenant context invalidation failed: {e}")
            return 0

    async def get_tenant_namespace_revision(self, tenant_id: str, namespace: str) -> int:
        """Return a tenant-local cache revision, falling back to the initial revision."""
        value = await self.get(tenant_namespace_revision_key(tenant_id, namespace))
        try:
            return int(value) if value is not None else 0
        except (TypeError, ValueError):
            return 0

    async def bump_tenant_namespace_revision(self, tenant_id: str, namespace: str) -> int:
        """Logically invalidate a tenant namespace by incrementing its revision."""
        if not self._client:
            return 0

        try:
            return int(await self._client.incr(tenant_namespace_revision_key(tenant_id, namespace)))
        except Exception as e:
            logger.error(f"Redis namespace revision update failed: {e}")
            return 0

    async def allow_rate_limit(self, key: str, limit: int, window: int) -> bool:
        """Atomically enforce a fixed-window limit when Redis is available."""
        if not self._client:
            return True
        try:
            count = await self._client.incr(key)
            if count == 1:
                await self._client.expire(key, window)
            return count <= limit
        except Exception as e:
            logger.error(f"Redis rate limit update failed: {e}")
            return True

    # ==================== Application-Specific Methods ====================
    
    async def cache_conversation(
        self, 
        organization_id: str,
        user_id: str, 
        conversation_id: str, 
        messages: List[Dict[str, Any]],
        ttl: int = 3600
    ) -> bool:
        """Cache conversation messages"""
        cache_key = build_cache_key(
            "conversation", {"user_id": user_id, "conversation_id": conversation_id}, tenant_id=organization_id
        )
        cache_data = {
            'messages': messages,
            'cached_at': datetime.now().isoformat(),
            'user_id': user_id,
            'conversation_id': conversation_id
        }
        return await self.set_json(cache_key, cache_data, ttl)
    
    async def get_cached_conversation(
        self, 
        organization_id: str,
        user_id: str, 
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached conversation"""
        cache_key = build_cache_key(
            "conversation", {"user_id": user_id, "conversation_id": conversation_id}, tenant_id=organization_id
        )
        return await self.get_json(cache_key)
    
    async def cache_user_context(
        self, 
        organization_id: str,
        user_id: str, 
        context: Dict[str, Any],
        ttl: int = 1800
    ) -> bool:
        """Cache user context for LLM"""
        cache_key = build_user_context_cache_key(organization_id, user_id)
        return await self.set_json(cache_key, context, ttl)
    
    async def get_user_context(self, organization_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user context"""
        cache_key = build_user_context_cache_key(organization_id, user_id)
        return await self.get_json(cache_key)
    
    async def clear_user_cache(self, organization_id: str, user_id: str) -> bool:
        """Clear direct tenant-local customer cache records for one user."""
        if not self._client:
            return False
        
        try:
            deleted_count = await self._client.delete(
                build_user_context_cache_key(organization_id, user_id),
                build_user_profile_cache_key(organization_id, user_id),
            )
            
            logger.info("Cleared tenant-local user cache", extra={"deleted": deleted_count})
            return True
            
        except Exception as e:
            logger.error(f"Error clearing user cache for {user_id}: {e}")
            return False
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self._client:
            return {"connected": False}
        
        try:
            info = await self._client.info()
            db_index = self.db
            if self._pool:
                db_index = int(self._pool.connection_kwargs.get("db", self.db))
            return {
                "connected": True,
                "total_keys": info.get(f"db{db_index}", {}).get("keys", 0)
                if isinstance(info.get(f"db{db_index}"), dict)
                else 0,
                "memory_usage": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}

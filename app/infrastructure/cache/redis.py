"""
Redis Cache Client
Layer 6: Infrastructure - Data & State
Pure CRUD operations, no business logic
"""
import json
import asyncio
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.asyncio import ConnectionPool

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
            await self._client.close()
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
    
    async def get_json(self, key: str) -> Optional[Dict[str, Any]]:
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
        value: Dict[str, Any], 
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
    
    # ==================== Application-Specific Methods ====================
    
    async def cache_conversation(
        self, 
        user_id: str, 
        conversation_id: str, 
        messages: List[Dict[str, Any]],
        ttl: int = 3600
    ) -> bool:
        """Cache conversation messages"""
        cache_key = f"conversation:{user_id}:{conversation_id}"
        cache_data = {
            'messages': messages,
            'cached_at': datetime.now().isoformat(),
            'user_id': user_id,
            'conversation_id': conversation_id
        }
        return await self.set_json(cache_key, cache_data, ttl)
    
    async def get_cached_conversation(
        self, 
        user_id: str, 
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached conversation"""
        cache_key = f"conversation:{user_id}:{conversation_id}"
        return await self.get_json(cache_key)
    
    async def cache_user_context(
        self, 
        user_id: str, 
        context: Dict[str, Any],
        ttl: int = 1800
    ) -> bool:
        """Cache user context for LLM"""
        cache_key = f"user_context:{user_id}"
        return await self.set_json(cache_key, context, ttl)
    
    async def get_user_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get cached user context"""
        cache_key = f"user_context:{user_id}"
        return await self.get_json(cache_key)
    
    async def clear_user_cache(self, user_id: str) -> bool:
        """Clear all cached data for a user"""
        if not self._client:
            return False
        
        try:
            patterns = [
                f"conversation:{user_id}:*",
                f"user_context:{user_id}",
                f"user_profile:{user_id}",
                f"user_activity:{user_id}:*"
            ]
            
            deleted_count = 0
            for pattern in patterns:
                keys = await self._client.keys(pattern)
                if keys:
                    deleted_count += await self._client.delete(*keys)
            
            logger.info(f"Cleared {deleted_count} cache keys for user {user_id}")
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
            return {
                "connected": True,
                "total_keys": info.get("db0", {}).get("keys", 0) if isinstance(info.get("db0"), dict) else 0,
                "memory_usage": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "uptime": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {"connected": False, "error": str(e)}

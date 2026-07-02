"""Cache infrastructure layer"""
from app.infrastructure.cache.redis import RedisClient as CacheClient

__all__ = ["CacheClient"]

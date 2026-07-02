"""
Short-term Memory - Layer 4: Add-ons
Session-based memory using Redis
"""
from typing import Any, Dict, List, Optional

from app.infrastructure.cache.redis import RedisClient


class ShortTermMemory:
    """Short-term memory for current session"""
    
    def __init__(self, cache: RedisClient):
        self.cache = cache
    
    async def get_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user context from cache"""
        if not self.cache:
            return None
        return await self.cache.get_json(f"user_context:{user_id}")
    
    async def save_context(self, user_id: str, context: Dict[str, Any], ttl: int = 1800) -> bool:
        """Save user context to cache"""
        if not self.cache:
            return False
        return await self.cache.set_json(f"user_context:{user_id}", context, ttl)
    
    async def get_conversation(self, user_id: str, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get cached conversation"""
        if not self.cache:
            return None
        return await self.cache.get_cached_conversation(user_id, conversation_id)
    
    async def save_conversation(self, user_id: str, conversation_id: str, messages: List[Dict[str, Any]]) -> bool:
        """Save conversation to cache"""
        if not self.cache:
            return False
        return await self.cache.cache_conversation(user_id, conversation_id, messages)

"""
Short-term Memory - Layer 4: Add-ons
Session-based memory using Redis
"""
from typing import Any, Dict, List, Optional

from app.infrastructure.cache.keys import build_cache_key, build_user_context_cache_key
from app.infrastructure.cache.redis import RedisClient


class ShortTermMemory:
    """Short-term memory for current session"""
    
    def __init__(self, cache: RedisClient):
        self.cache = cache
    
    async def get_context(self, organization_id: str, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user context from cache"""
        if not self.cache:
            return None
        return await self.cache.get_json(build_user_context_cache_key(organization_id, user_id))
    
    async def save_context(
        self, organization_id: str, user_id: str, context: Dict[str, Any], ttl: int = 1800
    ) -> bool:
        """Save user context to cache"""
        if not self.cache:
            return False
        return await self.cache.set_json(
            build_user_context_cache_key(organization_id, user_id), context, ttl
        )
    
    async def get_conversation(
        self, organization_id: str, user_id: str, conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get cached conversation"""
        if not self.cache:
            return None
        return await self.cache.get_json(
            build_cache_key(
                "conversation",
                {"user_id": user_id, "conversation_id": conversation_id},
                tenant_id=organization_id,
            )
        )
    
    async def save_conversation(
        self, organization_id: str, user_id: str, conversation_id: str, messages: List[Dict[str, Any]]
    ) -> bool:
        """Save conversation to cache"""
        if not self.cache:
            return False
        return await self.cache.set_json(
            build_cache_key(
                "conversation",
                {"user_id": user_id, "conversation_id": conversation_id},
                tenant_id=organization_id,
            ),
            messages,
            ttl=3600,
        )

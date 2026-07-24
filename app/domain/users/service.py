"""
User Service - Layer 5: Domain
Pure business logic
"""
from typing import Any, Dict, Optional

from app.infrastructure.cache.keys import build_user_profile_cache_key
from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.db.postgres import PostgresClient


class UserService:
    """User business logic"""

    def __init__(self, db: PostgresClient, cache: RedisClient):
        self.db = db
        self.cache = cache

    @staticmethod
    def _scope(organization_id: str, user_id: Optional[str]) -> tuple[str, str]:
        """Resolve legacy single-ID calls only from an already authenticated tenant context."""
        if user_id is not None:
            return organization_id, user_id
        from app.core.security.context import tenant_context_var

        tenant = tenant_context_var.get()
        if not tenant:
            raise ValueError("Tenant context required for customer data")
        return tenant.organization_id, organization_id

    async def get_user_profile(
        self, organization_id: str, user_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get user profile with caching"""
        organization_id, user_id = self._scope(organization_id, user_id)
        cache_key = build_user_profile_cache_key(organization_id, user_id)
        if self.cache:
            cached = await self.cache.get_json(cache_key)
            if cached:
                return cached

        profile = await self.db.get_user_profile(organization_id, user_id)
        if profile and self.cache:
            await self.cache.set_json(cache_key, profile, ttl=3600)

        return profile

    async def update_preferences(
        self,
        organization_id: str,
        user_id: Optional[str] = None,
        preferences: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update user preferences"""
        from app.infrastructure.id_generator import IDGenerator

        if preferences is None:
            # Legacy call shape: update_preferences(user_id, preferences).
            preferences = user_id if isinstance(user_id, dict) else {}
            organization_id, user_id = self._scope(organization_id, None)
        else:
            organization_id, user_id = self._scope(organization_id, user_id)

        success = await self.db.update_user(organization_id, user_id, {
            'preferences': preferences,
            'updated_at': IDGenerator.timestamp()
        })
        if success and self.cache:
            await self.cache.delete(build_user_profile_cache_key(organization_id, user_id))
        return success

    async def log_activity(
        self,
        organization_id: str,
        user_id: Optional[str] = None,
        activity_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Log user activity"""
        from app.infrastructure.id_generator import IDGenerator

        if metadata is None and isinstance(activity_type, dict):
            # Legacy call shape: log_activity(user_id, activity_type, metadata).
            metadata = activity_type
            activity_type = user_id
            organization_id, user_id = self._scope(organization_id, None)
        else:
            organization_id, user_id = self._scope(organization_id, user_id)

        activity_data = {
            'user_id': user_id,
            'activity_type': activity_type,
            'metadata': metadata or {},
            'timestamp': IDGenerator.timestamp()
        }

        # Save to user's activity subcollection
        activity_id = await self.db.log_user_activity(organization_id, activity_data)
        return activity_id is not None

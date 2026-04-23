"""
User Service - Layer 5: Domain
Pure business logic
"""
from typing import Any, Dict, Optional

from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.db.firestore import FirestoreClient


class UserService:
    """User business logic"""
    
    def __init__(self, firestore: FirestoreClient, cache: RedisClient):
        self.db = firestore
        self.cache = cache
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user profile with caching"""
        cached = await self.cache.get_json(f"user_profile:{user_id}")
        if cached:
            return cached
        
        profile = await self.db.get_document('users', user_id)
        if profile:
            await self.cache.set_json(f"user_profile:{user_id}", profile, ttl=3600)
        
        return profile
    
    async def update_preferences(self, user_id: str, preferences: Dict[str, Any]) -> bool:
        """Update user preferences"""
        from app.infrastructure.id_generator import IDGenerator
        
        success = await self.db.update_document('users', user_id, {
            'preferences': preferences,
            'updated_at': IDGenerator.timestamp()
        })
        if success:
            await self.cache.delete(f"user_profile:{user_id}")
        return success
    
    async def log_activity(self, user_id: str, activity_type: str, metadata: Dict[str, Any]) -> bool:
        """Log user activity"""
        from app.infrastructure.id_generator import IDGenerator
        
        activity_data = {
            'user_id': user_id,
            'activity_type': activity_type,
            'metadata': metadata,
            'timestamp': IDGenerator.timestamp()
        }
        
        # Save to user's activity subcollection
        activity_id = await self.db.add_to_subcollection('users', user_id, 'activities', activity_data)
        return activity_id is not None

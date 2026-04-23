"""
User Service
User profile management and activity tracking
"""
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger
from app.services.container import ServiceInterface

logger = get_logger("user")

class UserService(ServiceInterface):
    """Async user service for profile and activity management"""
    
    def __init__(self):
        self.firestore_service = None
        self.redis_service = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize user service"""
        self._initialized = True
        logger.info("✅ User service initialized")
    
    async def cleanup(self) -> None:
        """Cleanup user service"""
        self._initialized = False
        logger.info("✅ User service cleaned up")
    
    async def health_check(self) -> bool:
        """Check user service health"""
        return self._initialized
    
    def set_dependencies(self, firestore_service, redis_service):
        """Set service dependencies"""
        self.firestore_service = firestore_service
        self.redis_service = redis_service
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile with caching"""
        try:
            # Try cache first
            if self.redis_service:
                cached_profile = await self.redis_service.get_json(f"user_profile:{user_id}")
                if cached_profile:
                    return {
                        "success": True,
                        "data": cached_profile,
                        "cached": True
                    }
            
            # Get from Firestore
            if self.firestore_service:
                profile = await self.firestore_service.get_user_profile(user_id)
                if profile:
                    # Cache the profile
                    if self.redis_service:
                        await self.redis_service.set_json(
                            f"user_profile:{user_id}", 
                            profile, 
                            ttl=3600  # 1 hour
                        )
                    
                    return {
                        "success": True,
                        "data": profile,
                        "cached": False
                    }
            
            # Return default profile
            default_profile = {
                "user_id": user_id,
                "preferences": {},
                "created_at": datetime.now().isoformat(),
                "activity_summary": {}
            }
            
            return {
                "success": True,
                "data": default_profile,
                "cached": False
            }
            
        except Exception as e:
            logger.error(f"Error getting user profile for {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_user_preferences(
        self, 
        user_id: str, 
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user preferences"""
        try:
            # Update in Firestore
            if self.firestore_service:
                await self.firestore_service.update_user_preferences(user_id, preferences)
            
            # Clear cache
            if self.redis_service:
                await self.redis_service.delete(f"user_profile:{user_id}")
            
            return {
                "success": True,
                "message": "Preferences updated successfully"
            }
            
        except Exception as e:
            logger.error(f"Error updating preferences for {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def log_activity(
        self, 
        user_id: str, 
        activity_type: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Log user activity"""
        try:
            activity_data = {
                "user_id": user_id,
                "activity_type": activity_type,
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            
            # Store in Firestore
            if self.firestore_service:
                await self.firestore_service.log_user_activity(activity_data)
            
            # Update activity cache
            if self.redis_service:
                activity_key = f"user_activity:{user_id}:recent"
                await self.redis_service.lpush(activity_key, str(activity_data))
                # Keep only recent 100 activities
                await self.redis_service.ltrim(activity_key, 0, 99)
                await self.redis_service.expire(activity_key, 86400)  # 24 hours
            
            return {
                "success": True,
                "message": "Activity logged successfully"
            }
            
        except Exception as e:
            logger.error(f"Error logging activity for {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_user_activity(
        self, 
        user_id: str, 
        limit: int = 50
    ) -> Dict[str, Any]:
        """Get user activity history"""
        try:
            activities = []
            
            # Try cache first
            if self.redis_service:
                cached_activities = await self.redis_service.lrange(
                    f"user_activity:{user_id}:recent", 0, limit - 1
                )
                if cached_activities:
                    activities = [eval(activity) for activity in cached_activities]
            
            # If not enough from cache, get from Firestore
            if len(activities) < limit and self.firestore_service:
                firestore_activities = await self.firestore_service.get_user_activity(
                    user_id, limit
                )
                activities.extend(firestore_activities)
            
            return {
                "success": True,
                "activities": activities[:limit],
                "total": len(activities)
            }
            
        except Exception as e:
            logger.error(f"Error getting activity for {user_id}: {e}")
            return {
                "success": False,
                "error": str(e)
            }
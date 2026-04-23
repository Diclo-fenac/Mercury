"""
User Orchestrator - Layer 2: Orchestration
Coordinates user workflow
"""
from typing import Any, Dict

from app.domain.users.service import UserService


class UserOrchestrator:
    """Orchestrates user workflow"""
    
    def __init__(self, user_service: UserService):
        self.users = user_service
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        try:
            profile_data = await self.users.get_user_profile(user_id)
            
            if not profile_data:
                return {"success": False, "error": "not_found"}
            
            # Structure the profile response
            profile = {
                "user_id": user_id,
                "preferences": profile_data.get("preferences", {}),
                "activity_summary": profile_data.get("activity_summary", {}),
                "created_at": profile_data.get("created_at"),
                "last_active": profile_data.get("last_active")
            }
            
            return {
                "success": True,
                "profile": profile
            }
        except Exception as e:
            raise Exception(f"Failed to get user profile: {str(e)}")
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        try:
            profile_data = await self.users.get_user_profile(user_id)
            
            if not profile_data:
                return {"success": False, "error": "not_found"}
            
            return {
                "success": True,
                "preferences": profile_data.get("preferences", {}),
                "last_updated": profile_data.get("updated_at")
            }
        except Exception as e:
            raise Exception(f"Failed to get user preferences: {str(e)}")
    
    async def update_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences"""
        try:
            success = await self.users.update_preferences(user_id, preferences)
            
            if not success:
                raise Exception("Failed to update preferences in database")
            
            # Return the updated preferences
            updated_profile = await self.users.get_user_profile(user_id)
            return {
                "success": True,
                "preferences": updated_profile.get("preferences", {}) if updated_profile else preferences,
                "updated_at": updated_profile.get("updated_at") if updated_profile else None
            }
        except Exception as e:
            raise Exception(f"Failed to update user preferences: {str(e)}")
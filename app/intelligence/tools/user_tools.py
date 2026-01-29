"""
User Tools - Layer 3: Intelligence
Function calling tools for user operations
"""
from typing import Dict, Any
from app.domain.users.service import UserService


class UserTools:
    """User-related tools for LLM"""
    
    def __init__(self, user_service: UserService):
        self.users = user_service
    
    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences"""
        profile = await self.users.get_user_profile(user_id)
        return profile.get('preferences', {}) if profile else {}
    
    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile"""
        return await self.users.get_user_profile(user_id) or {}

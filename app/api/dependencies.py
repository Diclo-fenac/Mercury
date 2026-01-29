"""
API Dependencies
FastAPI dependency injection for services
"""
from typing import Dict, Any, Optional
from fastapi import Depends, HTTPException, status, Request
from app.container import get_container


async def get_container_dependency():
    """Get the service container"""
    return get_container()


async def get_product_service(container = Depends(get_container_dependency)):
    """Get product service"""
    return container.get('product_service')


async def get_user_service(container = Depends(get_container_dependency)):
    """Get user service"""
    return container.get('user_service')


async def get_search_service(container = Depends(get_container_dependency)):
    """Get search service"""
    return container.get('hybrid_search')


async def get_image_service(container = Depends(get_container_dependency)):
    """Get image service"""
    return container.get('image_processor')


async def get_conversation_service(container = Depends(get_container_dependency)):
    """Get conversation service"""
    return container.get('conversation_service')


async def get_chat_service(container = Depends(get_container_dependency)):
    """Get chat service"""
    return container.get('chat_orchestrator')


# Authentication (simplified for development)
async def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current user (optional) - simplified for development"""
    # In production, this would validate JWT tokens, API keys, etc.
    return None


async def require_auth() -> Dict[str, Any]:
    """Require authentication - simplified for development"""
    # In production, this would validate JWT tokens, API keys, etc.
    # For now, return a mock user for development
    return {
        "user_id": "dev_user_123",
        "email": "dev@example.com",
        "roles": ["user"]
    }
    
    # Production implementation would be:
    # token = get_token_from_header()
    # user = validate_jwt_token(token)
    # if not user:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    # return user


# Rate limiting (simple implementation)
async def check_rate_limit(key: str, limit: int = 60) -> bool:
    """Simple rate limiting"""
    return True


# Validation
def validate_user_id(user_id: str) -> str:
    """Validate user ID"""
    if not user_id or len(user_id) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    return user_id
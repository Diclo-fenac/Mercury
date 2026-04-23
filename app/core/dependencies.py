"""
FastAPI Dependencies
Dependency injection for services and utilities
"""
import asyncio
from functools import lru_cache
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.container import ServiceContainer

logger = get_logger("dependencies")
security = HTTPBearer(auto_error=False)

# Global service container
_service_container: Optional[ServiceContainer] = None

@lru_cache()
def get_service_container() -> ServiceContainer:
    """Get or create service container singleton"""
    global _service_container
    if _service_container is None:
        _service_container = ServiceContainer()
    return _service_container

async def get_redis_service():
    """Get Redis service dependency"""
    container = get_service_container()
    return await container.get_service("redis")

async def get_llm_service():
    """Get LLM service dependency"""
    container = get_service_container()
    return await container.get_service("llm")

async def get_user_service():
    """Get User service dependency"""
    container = get_service_container()
    return await container.get_service("user")

async def get_product_service():
    """Get Product service dependency"""
    container = get_service_container()
    return await container.get_service("product")

async def get_chat_service():
    """Get Chat service dependency"""
    container = get_service_container()
    return await container.get_service("chat")

async def get_conversation_service():
    """Get Conversation service dependency"""
    container = get_service_container()
    return await container.get_service("conversation")

async def get_image_service():
    """Get Image processing service dependency"""
    container = get_service_container()
    return await container.get_service("image_processing")

async def get_search_service():
    """Get Search service dependency"""
    container = get_service_container()
    return await container.get_service("search")

# Authentication dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from token (optional)
    Returns None if no token provided (for public endpoints)
    """
    if not credentials:
        return None
    
    try:
        # TODO: Implement proper JWT token validation
        # For now, just extract user_id from token
        token = credentials.credentials
        
        # Simple token validation (replace with proper JWT)
        if token.startswith("user_"):
            user_id = token.replace("user_", "")
            return {"user_id": user_id, "authenticated": True}
        
        return None
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return None

async def require_auth(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require authentication"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user

# Rate limiting dependency
class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self._requests: Dict[str, list] = {}
        self._lock = asyncio.Lock()
    
    async def check_rate_limit(self, key: str, limit: int = 60, window: int = 60) -> bool:
        """Check if request is within rate limit"""
        import time
        
        async with self._lock:
            now = time.time()
            
            # Clean old requests
            if key in self._requests:
                self._requests[key] = [
                    req_time for req_time in self._requests[key]
                    if now - req_time < window
                ]
            else:
                self._requests[key] = []
            
            # Check limit
            if len(self._requests[key]) >= limit:
                return False
            
            # Add current request
            self._requests[key].append(now)
            return True

rate_limiter = RateLimiter()

async def check_rate_limit(
    request_key: str = "global",
    limit: int = 60
) -> bool:
    """Rate limiting dependency"""
    if not await rate_limiter.check_rate_limit(request_key, limit):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return True

# Validation dependencies
def validate_user_id(user_id: str) -> str:
    """Validate user ID format"""
    if not user_id or len(user_id) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    return user_id

def validate_conversation_id(conversation_id: str) -> str:
    """Validate conversation ID format"""
    if not conversation_id or len(conversation_id) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID"
        )
    return conversation_id

# Settings dependency
def get_app_settings():
    """Get application settings"""
    return get_settings()

# Health check dependencies
async def check_service_health() -> Dict[str, Any]:
    """Check health of all services"""
    container = get_service_container()
    health_status = {}
    
    try:
        # Check Redis
        redis_service = await container.get_service("redis")
        health_status["redis"] = await redis_service.is_available() if redis_service else False
        
        # Check other services
        services = ["llm", "user", "product", "chat"]
        for service_name in services:
            try:
                service = await container.get_service(service_name)
                health_status[service_name] = service is not None
            except Exception:
                health_status[service_name] = False
        
        return health_status
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {"error": str(e)}
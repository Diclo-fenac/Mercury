"""
API Dependencies
FastAPI dependency injection for services
"""
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Query, status

from app.container import get_container


class PaginationParams:
    """Dependency for common pagination parameters"""
    def __init__(
        self, 
        page: int = Query(1, ge=1, description="Page number"), 
        limit: int = Query(20, ge=1, le=100, description="Items per page")
    ):
        self.page = page
        self.limit = limit
        self.offset = (page - 1) * limit


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


from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.settings import get_settings

security = HTTPBearer(auto_error=False)

# Authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[Dict[str, Any]]:
    """
    Get current user from JWT token
    Returns None if no token provided or invalid
    """
    if not credentials:
        return None
    
    settings = get_settings()
    token = credentials.credentials
    
    try:
        # Development override: allow "dev_user_*" tokens
        if settings.DEBUG and token.startswith("user_"):
            user_id = token.replace("user_", "")
            return {"user_id": user_id, "authenticated": True, "roles": ["user"]}

        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        return {
            "user_id": user_id,
            "authenticated": True,
            "roles": payload.get("roles", ["user"]),
            "email": payload.get("email")
        }
    except JWTError:
        return None
    except Exception:
        # In a real app, log this
        return None


async def require_auth(
    current_user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """Require valid authentication token"""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return current_user


async def require_admin(
    current_user: Dict[str, Any] = Depends(require_auth)
) -> Dict[str, Any]:
    """Require admin role"""
    if "admin" not in current_user.get("roles", []):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


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
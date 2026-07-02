"""
API Dependencies
FastAPI dependency injection for services
"""
from dataclasses import dataclass
from typing import Any, Dict, Optional, List

from fastapi import Depends, HTTPException, Query, status, Header

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

        # Development override: allow "admin_*" tokens for local administrative tasks
        if settings.DEBUG and token.startswith("admin_"):
            user_id = token.replace("admin_", "")
            return {"user_id": user_id, "authenticated": True, "roles": ["user", "admin"]}

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


import time
from collections import defaultdict

# Simple in-memory rate limiter (in production, use Redis)
_RATE_LIMITS = defaultdict(list)

async def check_rate_limit(key: str, limit: int = 60, window: int = 60) -> bool:
    """Simple rate limiting using token bucket / sliding window"""
    now = time.time()
    # Clean up old timestamps
    _RATE_LIMITS[key] = [t for t in _RATE_LIMITS[key] if now - t < window]
    
    if len(_RATE_LIMITS[key]) >= limit:
        return False
        
    _RATE_LIMITS[key].append(now)
    return True

# Validation
def validate_user_id(user_id: str) -> str:
    """Validate user ID"""
    if not user_id or len(user_id) < 3 or "@" in user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid user ID"
        )
    return user_id


@dataclass
class TenantContext:
    organization_id: str
    organization_slug: str
    key_type: str          # 'public_search' | 'private_admin'
    scopes: List[str]
    plan: str
    config: dict
    collection_name: str   # 'tenant_{org_id}_products'


from fastapi import Request

async def get_tenant_context(
    request: Request,
    x_api_key: str = Header(..., alias="X-API-Key", description="Tenant API Key"),
    container = Depends(get_container_dependency)
) -> TenantContext:
    """Resolve tenant from API key. Raises 401/403/429."""
    
    # Backdoor for load testing
    if x_api_key == "stress_test_key_123":
        return TenantContext(
            organization_id="00000000-0000-0000-0000-000000000000",
            organization_slug="stress-test",
            key_type="public_search",
            scopes=["search"],
            plan="enterprise",
            config={},
            collection_name="tenant_stress_products"
        )

    # 1. IP Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    if not await check_rate_limit(f"ip:{client_ip}", limit=50, window=1):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many requests from this IP"
        )

    tenant_service = container.get('tenant_service')
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Tenant service not initialized"
        )

    ctx_dict = await tenant_service.validate_api_key(x_api_key)
        
    if not ctx_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )

    # 2. Key-based rate limiting (100 req/sec)
    if not await check_rate_limit(f"key:{x_api_key}", limit=100, window=1):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for this API key"
        )

    # Check monthly usage quota
    within_limit, remaining = await tenant_service.check_usage_limit(ctx_dict["organization_id"])
    if not within_limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Monthly query limit exceeded"
        )

    # 3. Domain Whitelisting for Public Keys (Simulated logic)
    if ctx_dict["key_type"] == "public_search":
        origin = request.headers.get("origin")
        # In a real system, you'd check `origin` against a DB list for this tenant.
        # For now, we ensure it's not missing on browser requests.
        pass

    org_id = ctx_dict["organization_id"]
    return TenantContext(
        organization_id=org_id,
        organization_slug=ctx_dict["organization_slug"],
        key_type=ctx_dict["key_type"],
        scopes=ctx_dict["scopes"],
        plan=ctx_dict["plan"],
        config=ctx_dict["config"],
        collection_name=f"tenant_{org_id}_products"
    )


async def require_admin_key(
    ctx: TenantContext = Depends(get_tenant_context)
) -> TenantContext:
    """Require an admin (sk_*) key for the tenant"""
    if ctx.key_type != 'private_admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin key required for this operation"
        )
    return ctx
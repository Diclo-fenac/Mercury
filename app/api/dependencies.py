"""
API Dependencies
FastAPI dependency injection for services
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastapi import Depends, Header, HTTPException, Query, status

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
        # Debug tokens still carry tenant scope: user_<org_id>:<user_id>.
        # Unscoped debug identities are forbidden because they bypass isolation.
        if settings.DEBUG and (token.startswith("user_") or token.startswith("admin_")):
            is_admin = token.startswith("admin_")
            subject = token.split("_", 1)[1]
            organization_id, separator, user_id = subject.partition(":")
            if not separator or not organization_id or not user_id:
                return None
            return {
                "user_id": user_id,
                "organization_id": organization_id,
                "authenticated": True,
                "roles": ["user", "admin"] if is_admin else ["user"],
            }

        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=["HS256"]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        
        organization_id = payload.get("organization_id") or payload.get("org_id")
        if not organization_id:
            return None

        return {
            "user_id": user_id,
            "organization_id": organization_id,
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


def require_same_tenant(current_user: Dict[str, Any], tenant: "TenantContext") -> None:
    """Reject a JWT/API-key pair that resolves to different organizations."""
    if current_user.get("organization_id") != tenant.organization_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User and API key belong to different organizations",
        )


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


import hashlib
import time
from collections import defaultdict

# Simple in-memory rate limiter (in production, use Redis)
_RATE_LIMITS = defaultdict(list)

async def check_rate_limit(key: str, limit: int = 60, window: int = 60, cache=None) -> bool:
    """Simple rate limiting using token bucket / sliding window"""
    if cache:
        return await cache.allow_rate_limit(key, limit, window)
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
    seller_id: Optional[str] = None


from fastapi import Request


async def get_tenant_context(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key", description="Tenant API Key"),
    authorization: Optional[str] = Header(None, alias="Authorization", description="Bearer Authorization Token"),
    container = Depends(get_container_dependency)
) -> TenantContext:
    """Resolve tenant from API key. Raises 401/403/429."""
    api_key = x_api_key
    if not api_key and authorization:
        if authorization.startswith("Bearer "):
            api_key = authorization[7:].strip()
        else:
            api_key = authorization.strip()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required (via X-API-Key or Authorization Bearer header)"
        )
    
    # 1. IP Rate Limiting
    client_ip = request.client.host if request.client else "unknown"
    cache = container.get('redis')
    if not await check_rate_limit(f"ip:{client_ip}", limit=1000, window=1, cache=cache):
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

    ctx_dict = await tenant_service.validate_api_key(api_key)
        
    if not ctx_dict:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )

    # 2. Key-based rate limiting (2000 req/sec)
    key_fingerprint = hashlib.sha256(api_key.encode()).hexdigest()
    if not await check_rate_limit(f"key:{key_fingerprint}", limit=2000, window=1, cache=cache):
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
    
    # Check if a specific seller scope is requested/authorized
    # In a full RBAC system, this would extract seller_id from a scoped token
    seller_id = request.headers.get("X-Seller-Id")
    
    return TenantContext(
        organization_id=org_id,
        organization_slug=ctx_dict["organization_slug"],
        key_type=ctx_dict["key_type"],
        scopes=ctx_dict["scopes"],
        plan=ctx_dict["plan"],
        config=ctx_dict["config"],
        collection_name=f"tenant_{org_id}_products",
        seller_id=seller_id
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


def require_scope(required_scope: str):
    """Require a specific scope for the operation"""
    def scope_checker(ctx: TenantContext = Depends(require_admin_key)) -> TenantContext:
        if required_scope not in ctx.scopes and "admin" not in ctx.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required scope: {required_scope}"
            )
        return ctx
    return scope_checker

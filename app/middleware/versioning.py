"""
Versioning and Feature Flags Middleware
Injects versioning and feature flag headers into all responses
"""
from starlette.middleware.base import BaseHTTPMiddleware

from app.settings import get_settings


class VersioningMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        settings = get_settings()
        response = await call_next(request)
        
        # Add API version header
        response.headers["X-API-Version"] = settings.VERSION
        
        # Add feature flags header if configured
        if hasattr(settings, "FEATURE_FLAGS") and settings.FEATURE_FLAGS:
            response.headers["X-Feature-Flags"] = ",".join(settings.FEATURE_FLAGS)
            
        # Example of deprecation logic
        if request.url.path.startswith("/api/v1/old-endpoint"):
            response.headers["Deprecation"] = "true"
            response.headers["Link"] = '<https://api.mercury.com/docs/deprecation>; rel="deprecation"'
            
        return response

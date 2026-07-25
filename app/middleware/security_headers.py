"""
Security Headers Middleware

Adds hardened security response headers to all responses.
The widget endpoints are public (CORS is open) but still benefit from
these defensive headers.
"""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to every response.
    Does NOT add HSTS (that belongs at the load-balancer/CDN layer).
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        response: Response = await call_next(request)

        # Prevent MIME-type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Prevent clickjacking (dashboard and admin pages)
        if not request.url.path.startswith("/widget/"):
            response.headers["X-Frame-Options"] = "DENY"

        # Block XSS in older browsers (belt-and-suspenders)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer policy – don't leak the full URL in referer headers
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions policy – deny access to sensitive device APIs
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
        )

        # Remove server fingerprinting header (uvicorn adds this)
        try:
            del response.headers["server"]
        except KeyError:
            pass

        return response

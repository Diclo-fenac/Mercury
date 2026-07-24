from fastapi import Request, Response
from mcp.server.fastmcp import FastMCP

from app.mcp.auth import authenticate_mcp_request
from app.mcp.context import reset_mcp_tenant_context, set_mcp_tenant_context

# Create the FastMCP Server instance
mcp = FastMCP("mercury-mcp", dependencies=[])

class MCPAuthMiddleware:
    """
    ASGI middleware to enforce Tenant Context and authentication for MCP endpoints.
    """
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        request = Request(scope, receive)

        # Extract credentials
        api_key = request.headers.get("x-api-key")
        auth_header = request.headers.get("authorization")
        bearer = None
        if auth_header and auth_header.startswith("Bearer "):
            from fastapi.security import HTTPAuthorizationCredentials
            bearer = HTTPAuthorizationCredentials(scheme="Bearer", credentials=auth_header[7:])

        try:
            tenant_context = await authenticate_mcp_request(request, api_key=api_key, bearer=bearer)
        except Exception as e:
            # Unauthorized or internal error
            if scope["type"] == "http":
                import json
                detail = getattr(e, "detail", "Unauthorized")
                status_code = getattr(e, "status_code", 401)

                await send({
                    "type": "http.response.start",
                    "status": status_code,
                    "headers": [(b"content-type", b"application/json")],
                })
                await send({
                    "type": "http.response.body",
                    "body": json.dumps({"detail": detail}).encode("utf-8"),
                })
            elif scope["type"] == "websocket":
                await send({"type": "websocket.close", "code": 1008})
            return

        token = set_mcp_tenant_context(tenant_context)
        try:
            await self.app(scope, receive, send)
        finally:
            reset_mcp_tenant_context(token)

def get_mcp_app():
    """
    Returns the authenticated ASGI application for MCP.
    """
    # Force import of tools so they register with FastMCP
    from app.mcp.tools import catalog, chat, recommendations, search

    # Get the raw Starlette app from FastMCP
    raw_app = mcp.sse_app()

    # Wrap in authentication middleware
    return MCPAuthMiddleware(raw_app)

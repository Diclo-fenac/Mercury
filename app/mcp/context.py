import contextvars
from typing import Optional

from app.api.dependencies import TenantContext

# Context variable to hold the current tenant context for MCP tool execution
_mcp_tenant_context: contextvars.ContextVar[Optional[TenantContext]] = contextvars.ContextVar(
    "mcp_tenant_context", default=None
)

def get_mcp_tenant_context() -> TenantContext:
    """Get the current tenant context. Raises error if not set."""
    ctx = _mcp_tenant_context.get()
    if not ctx:
        raise RuntimeError("MCP TenantContext is not set for the current request.")
    return ctx

def set_mcp_tenant_context(ctx: TenantContext) -> contextvars.Token:
    """Set the current tenant context."""
    return _mcp_tenant_context.set(ctx)

def reset_mcp_tenant_context(token: contextvars.Token) -> None:
    """Reset the tenant context using the token."""
    _mcp_tenant_context.reset(token)

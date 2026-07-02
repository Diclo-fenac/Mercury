import contextvars
from typing import Any, Optional

tenant_context_var: contextvars.ContextVar[Optional[Any]] = contextvars.ContextVar("tenant_context", default=None)
user_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("user_id", default=None)

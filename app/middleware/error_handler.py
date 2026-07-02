import logging
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

async def global_exception_handler(request: Request, exc: Exception):
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    logger.error(
        f"Unhandled exception: {str(exc)}",
        exc_info=True,
        extra={"event": "error", "trace_id": trace_id}
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Falling back to search only.",
                "trace_id": trace_id
            }
        }
    )

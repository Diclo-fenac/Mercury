"""
FastAPI Main Application
Clean architecture implementation
"""
import asyncio
import logging
from asyncio import CancelledError, create_task, sleep
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager, suppress

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.container import get_container
from app.middleware.versioning import VersioningMiddleware
from app.settings import get_settings
from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


async def _run_catalog_index_worker(worker, settings) -> None:
    """Continuously replay durable catalog index events while this process is alive."""
    while True:
        try:
            result = await worker.run_once(settings.CATALOG_INDEX_BATCH_SIZE)
            # Yield after a full batch so requests and other background tasks run fairly.
            await sleep(0 if result["claimed"] else settings.CATALOG_INDEX_POLL_INTERVAL_SECONDS)
        except CancelledError:
            raise
        except Exception:
            logger.exception("Catalog index worker iteration failed")
            await sleep(settings.CATALOG_INDEX_POLL_INTERVAL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting application")
    loop = asyncio.get_running_loop()
    loop.set_default_executor(ThreadPoolExecutor(max_workers=200))
    settings = get_settings()
    container = get_container()
    if settings.TEST_MODE:
        # Endpoint tests provide dependency overrides; never boot external services.
        app.state.container = container
        yield
        return

    await container.initialize()
    app.state.container = container
    worker_task = None
    worker = container.get("catalog_index_worker")
    if settings.CATALOG_INDEX_WORKER_ENABLED and worker:
        worker_task = create_task(
            _run_catalog_index_worker(worker, settings), name="catalog-index-worker"
        )

    try:
        yield
    finally:
        if worker_task:
            worker_task.cancel()
            with suppress(CancelledError):
                await worker_task
        logger.info("Shutting down application")
        await container.cleanup()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Mercury AI Assistant",
        version="4.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan
    )
    
    origins = settings.ALLOWED_ORIGINS
    if "*" in origins:
        if settings.DEBUG:
            origins = [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ]
        else:
            logger.warning("Wildcard '*' in ALLOWED_ORIGINS is not allowed in production with allow_credentials=True.")
            origins = []

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    app.add_middleware(VersioningMiddleware)
    
    # Add global exception handler
    from app.middleware.error_handler import global_exception_handler
    app.add_exception_handler(Exception, global_exception_handler)
    
    # Include main API router with all endpoints
    app.include_router(api_router, prefix="/api/v1")
    
    # Mount Dashboard
    import os

    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles

    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard")
    if not os.path.exists(dashboard_path):
        dashboard_path = os.path.abspath("dashboard")

    widget_path = os.path.join(os.path.dirname(__file__), "widget")
    if not os.path.exists(widget_path):
        widget_path = os.path.abspath("widget")
    if os.path.exists(dashboard_path):
        app.mount("/dashboard/static", StaticFiles(directory=dashboard_path), name="dashboard_static")
        
        @app.get("/dashboard", include_in_schema=False)
        async def serve_dashboard():
            return FileResponse(os.path.join(dashboard_path, "index.html"))
            
        @app.get("/dashboard/demo", include_in_schema=False)
        async def serve_demo():
            return FileResponse(os.path.join(dashboard_path, "demo.html"))

    if settings.MCP_ENABLED:
        from app.mcp.server import get_mcp_app
        app.mount("/api/v1/mcp", get_mcp_app())
    
    # Serve static widget scripts
    if os.path.exists(widget_path):
        app.mount("/widget", StaticFiles(directory=widget_path), name="widget")
    
    # WebSocket endpoint mounting
    from fastapi import WebSocket, WebSocketDisconnect
    from fastapi.security import HTTPAuthorizationCredentials

    from app.api.dependencies import TenantContext, get_current_user
    from app.websocket.handlers import register_websocket_handlers
    from app.websocket.manager import WebSocketManager
    
    ws_manager = WebSocketManager()
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        container = get_container()
        api_key = websocket.headers.get("x-api-key")
        authorization = websocket.headers.get("authorization", "")
        if not api_key or not authorization.startswith("Bearer "):
            await websocket.close(code=1008, reason="Tenant API key and JWT required")
            return

        tenant_service = container.get("tenant_service")
        if not tenant_service:
            await websocket.close(code=1011, reason="Tenant service unavailable")
            return
        tenant_data = await tenant_service.validate_api_key(api_key)
        current_user = await get_current_user(
            HTTPAuthorizationCredentials(
                scheme="Bearer", credentials=authorization.removeprefix("Bearer ")
            )
        )
        if not tenant_data or not current_user or current_user.get("organization_id") != tenant_data["organization_id"]:
            await websocket.close(code=1008, reason="Invalid tenant credentials")
            return

        tenant_context = TenantContext(
            organization_id=tenant_data["organization_id"],
            organization_slug=tenant_data["organization_slug"],
            key_type=tenant_data["key_type"],
            scopes=tenant_data["scopes"],
            plan=tenant_data["plan"],
            config=tenant_data["config"],
            collection_name=f"tenant_{tenant_data['organization_id']}_products",
        )
        await ws_manager.connect(
            websocket,
            user_id=current_user["user_id"],
            organization_id=tenant_context.organization_id,
        )
        try:
            await register_websocket_handlers(
                websocket, ws_manager, container, tenant_context, current_user
            )
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
        except Exception as e:
            logger.error(f"WebSocket session error: {e}")
            ws_manager.disconnect(websocket)
    
    @app.get("/")
    async def root():
        return {"message": "Mercury AI Assistant API", "version": "4.0.0"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/metrics")
    async def metrics():
        from fastapi import Response

        from app.utils.metrics import CONTENT_TYPE_LATEST, generate_latest
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    # Use multiple workers in production to fix tail latency under high concurrency
    workers = 1 if settings.DEBUG else 4
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=workers
    )

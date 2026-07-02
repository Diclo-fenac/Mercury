"""
FastAPI Main Application
Clean architecture implementation
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.container import get_container
from app.middleware.versioning import VersioningMiddleware
from app.settings import get_settings
from app.utils.logger import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    logger.info("Starting application")
    
    container = get_container()
    await container.initialize()
    app.state.container = container
    
    yield
    
    logger.info("Shutting down application")
    await container.cleanup()


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()
    
    app = FastAPI(
        title="Mercury AI Assistant",
        version="4.0.0",
        docs_url="/docs" if settings.DEBUG else None,
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
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import FileResponse

    dashboard_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "dashboard")
    if os.path.exists(dashboard_path):
        app.mount("/dashboard/static", StaticFiles(directory=dashboard_path), name="dashboard_static")
        
        @app.get("/dashboard", include_in_schema=False)
        async def serve_dashboard():
            return FileResponse(os.path.join(dashboard_path, "index.html"))
            
        @app.get("/dashboard/demo", include_in_schema=False)
        async def serve_demo():
            return FileResponse(os.path.join(dashboard_path, "demo.html"))
    
    # Serve static widget scripts
    app.mount("/widget", StaticFiles(directory="widget"), name="widget")
    
    # WebSocket endpoint mounting
    from fastapi import WebSocket, WebSocketDisconnect
    from app.websocket.manager import WebSocketManager
    from app.websocket.handlers import register_websocket_handlers
    
    ws_manager = WebSocketManager()
    
    @app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket):
        await ws_manager.connect(websocket)
        try:
            from app.core.dependencies import get_service_container
            legacy_container = get_service_container()
            await register_websocket_handlers(websocket, ws_manager, legacy_container)
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

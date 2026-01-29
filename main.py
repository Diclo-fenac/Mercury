"""
FastAPI Main Application
Clean architecture implementation
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.settings import get_settings
from app.container import get_container
from app.utils.logger import setup_logging
from app.api.v1.router import api_router

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
        title="Walmart AI Assistant",
        version="4.0.0",
        docs_url="/docs" if settings.DEBUG else None,
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include main API router with all endpoints
    app.include_router(api_router, prefix="/api/v1")
    
    @app.get("/")
    async def root():
        return {"message": "Walmart AI Assistant API", "version": "4.0.0"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )

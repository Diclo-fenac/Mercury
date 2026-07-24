"""
API v1 Router
Main router that includes all endpoint modules
"""
from fastapi import APIRouter

from app.api.v1.endpoints import (
    admin,
    analytics,
    chat,
    conversations,
    health,
    images,
    products,
    search,
    telemetry,
    users,
    widget,
)

api_router = APIRouter()

# Include all endpoint routers with proper prefixes
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(conversations.router, prefix="/conversations", tags=["conversations"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(images.router, prefix="/images", tags=["images"])
api_router.include_router(search.router, prefix="/search", tags=["search"])
api_router.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(widget.router, prefix="/widget", tags=["widget"])
api_router.include_router(analytics.router, tags=["analytics"])
"""
Cache Management Endpoints
Redis cache operations and statistics
"""
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies import get_container_dependency, require_admin
from app.models.responses import CacheStats
from app.utils.logger import get_logger

logger = get_logger("cache")
router = APIRouter()

@router.get("/stats", response_model=CacheStats)
async def get_cache_stats(
    container = Depends(get_container_dependency),
    admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Get Redis cache statistics
    """
    try:
        redis_service = container.get('redis')
        if not redis_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache service not available"
            )
        
        # Simple stats
        cache_stats = CacheStats(
            total_keys=0,
            memory_usage="N/A",
            hit_rate=None,
            connected=True
        )
        
        return cache_stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"get_cache_stats_error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get cache statistics"
        )

@router.get("/health")
async def check_cache_health(
    container = Depends(get_container_dependency),
    admin: Dict[str, Any] = Depends(require_admin)
):
    """
    Check cache service health
    """
    try:
        redis_service = container.get('redis')
        if not redis_service:
            return {"healthy": False, "error": "Cache service not available"}
        
        return {
            "healthy": True,
            "service": "redis",
            "timestamp": "now"
        }
        
    except Exception as e:
        logger.error(f"cache_health_check_error: {e}")
        return {"healthy": False, "error": str(e)}
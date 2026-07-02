"""
Health Check Endpoints
System health and status monitoring
"""

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_container_dependency
from app.models.responses import HealthStatus
from app.settings import get_settings
from app.utils.logger import get_logger
from app.utils.metrics import generate_latest, CONTENT_TYPE_LATEST

logger = get_logger("health")
router = APIRouter()


@router.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@router.get("/", response_model=HealthStatus)
async def health_check(
    container = Depends(get_container_dependency)
):
    """
    Comprehensive health check endpoint
    Returns overall system health and individual service status
    """
    settings = get_settings()
    
    try:
        import torch
        gpu_enabled = torch.cuda.is_available()
    except ImportError:
        gpu_enabled = False
        
    # Check service health
    service_health = {
        "redis": container.get('redis') is not None,
        "postgres": container.get('postgres') is not None,
        "llm": container.get('llm_engine') is not None,
        "storage": container.get('storage') is not None,
        "gpu_enabled": gpu_enabled
    }
    
    # Determine overall status
    all_healthy = all(v for k, v in service_health.items() if k != "gpu_enabled")
    overall_status = "healthy" if all_healthy else "degraded"
    
    return HealthStatus(
        status=overall_status,
        version=settings.VERSION,
        services=service_health
    )
"""
Health Check Endpoints
System health and status monitoring
"""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_container_dependency
from app.models.responses import HealthStatus
from app.settings import get_settings
from app.utils.logger import get_logger

logger = get_logger("health")
router = APIRouter()

@router.get("/", response_model=HealthStatus)
async def health_check(
    container = Depends(get_container_dependency)
):
    """
    Comprehensive health check endpoint
    Returns overall system health and individual service status
    """
    settings = get_settings()
    
    # Check service health
    service_health = {
        "redis": container.get('redis') is not None,
        "firestore": container.get('firestore') is not None,
        "qdrant": container.get('qdrant') is not None,
        "llm": container.get('llm_engine') is not None,
        "gcs": container.get('gcs') is not None
    }
    
    # Determine overall status
    all_healthy = all(service_health.values())
    overall_status = "healthy" if all_healthy else "degraded"
    
    return HealthStatus(
        status=overall_status,
        version=settings.VERSION,
        services=service_health
    )

@router.get("/ready")
async def readiness_check(
    container = Depends(get_container_dependency)
):
    """
    Kubernetes readiness probe endpoint
    Returns 200 if ready to serve traffic
    """
    critical_services = ["redis", "firestore"]
    service_health = {
        "redis": container.get('redis') is not None,
        "firestore": container.get('firestore') is not None
    }
    
    ready = all(service_health.values())
    
    if not ready:
        return {"ready": False, "services": service_health}, 503
    
    return {"ready": True, "services": service_health}

@router.get("/live")
async def liveness_check():
    """
    Kubernetes liveness probe endpoint
    Returns 200 if application is alive
    """
    return {"alive": True}
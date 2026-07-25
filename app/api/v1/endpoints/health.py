"""
Health Check Endpoints
System health and status monitoring
"""

from fastapi import APIRouter, Depends, Response, Request

from app.api.dependencies import get_container_dependency
from app.models.responses import HealthStatus
from app.settings import get_settings
from app.utils.logger import get_logger
from app.utils.metrics import CONTENT_TYPE_LATEST, generate_latest

logger = get_logger("health")
router = APIRouter()


@router.get("/metrics")
async def metrics(request: Request):
    """Prometheus metrics endpoint (Internal IP restricted)"""
    client_ip = request.client.host if request.client else ""
    if not (client_ip.startswith("10.") or client_ip.startswith("172.") or client_ip.startswith("192.168.") or client_ip in ("127.0.0.1", "::1")):
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Metrics restricted to internal network")
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@router.get("/live")
async def liveness_check():
    """Liveness probe: returns 200 if process is running without checking external dependencies."""
    return {"status": "alive"}


@router.get("/ready", response_model=HealthStatus)
async def readiness_check(
    response: Response,
    container = Depends(get_container_dependency)
):
    """
    Readiness probe: checks required dependencies (Postgres, Redis, Typesense) with short timeouts.
    Returns 503 if any required service is unhealthy.
    """
    settings = get_settings()
    
    postgres_client = container.get('postgres')
    redis_client = container.get('redis')
    typesense_client = container.get('typesense')
    
    pg_ok = await postgres_client.health_check() if postgres_client else False
    redis_ok = await redis_client.health_check() if redis_client else False
    ts_ok = await typesense_client.health_check() if typesense_client else False
    
    service_health = {
        "postgres": pg_ok,
        "redis": redis_ok,
        "typesense": ts_ok
    }
    
    all_healthy = pg_ok and redis_ok and ts_ok
    overall_status = "healthy" if all_healthy else "degraded"
    
    if not all_healthy:
        response.status_code = 503
        
    return HealthStatus(
        status=overall_status,
        version=settings.VERSION,
        services=service_health
    )


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
        "typesense": container.get('typesense') is not None,
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
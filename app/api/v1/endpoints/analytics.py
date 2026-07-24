"""
Analytics Endpoints - Layer 1: API
Expose dashboard metrics for merchants
"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_admin
from app.container import Container
from app.domain.analytics.dashboard import DashboardService

router = APIRouter(prefix="/analytics", tags=["analytics"])


def get_dashboard_service() -> DashboardService:
    container = Container()
    return DashboardService(db=container.db())


@router.get("/dashboard")
async def get_dashboard(
    days: int = 30,
    service: DashboardService = Depends(get_dashboard_service),
    admin_user: dict = Depends(require_admin)
):
    """Get aggregated metrics for the merchant dashboard"""
    organization_id = admin_user.get("organization_id")
    if not organization_id:
        raise HTTPException(status_code=403, detail="Not associated with an organization")

    metrics = await service.get_dashboard_metrics(organization_id, days)
    if "error" in metrics:
        raise HTTPException(status_code=500, detail=metrics["error"])

    return metrics

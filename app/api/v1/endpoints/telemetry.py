from typing import Optional, Dict, Any
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import get_tenant_context, TenantContext, get_container_dependency
from app.models.responses import BaseResponse

router = APIRouter()

class TelemetryEvent(BaseModel):
    event_type: str = Field(..., description="Type of event (e.g., 'click')")
    search_id: Optional[str] = Field(None, description="The search ID this event originated from")
    product_id: Optional[str] = Field(None, description="The product ID that was interacted with")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

@router.post("/events", response_model=BaseResponse)
async def log_telemetry_event(
    event: TelemetryEvent,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """
    Log a telemetry event (like a product click) to power trending analytics.
    """
    if event.event_type == "click" and event.product_id:
        cache = container.get('cache')
        if not cache:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Cache service unavailable"
            )
            
        telemetry_key = f"telemetry:{tenant.organization_id}:trending_products:7d"
        
        # Increment the score for this product in the sorted set
        background_tasks.add_task(
            cache.zincrby,
            key=telemetry_key,
            amount=1.0,
            member=event.product_id
        )
        
    return BaseResponse(success=True, message="Event logged successfully")

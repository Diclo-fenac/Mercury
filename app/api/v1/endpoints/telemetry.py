from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.dependencies import TenantContext, get_container_dependency, get_tenant_context
from app.models.responses import BaseResponse

router = APIRouter()

class TelemetryEvent(BaseModel):
    event_type: str = Field(..., description="Type of event (e.g., 'click')")
    search_id: Optional[str] = Field(None, description="The search ID this event originated from")
    product_id: Optional[str] = Field(None, description="The product ID that was interacted with")
    query: Optional[str] = Field(None, description="The search query associated with the event")
    user_id: Optional[str] = Field(None, description="The user ID")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context")

@router.post("/events", response_model=BaseResponse, status_code=status.HTTP_202_ACCEPTED)
async def log_telemetry_event(
    event: TelemetryEvent,
    background_tasks: BackgroundTasks,
    tenant: TenantContext = Depends(get_tenant_context),
    container = Depends(get_container_dependency)
):
    """
    Log a telemetry event (like a product click) to power trending analytics.
    """
    cache = container.get('redis')
    if not cache:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cache service unavailable"
        )
        
    if event.event_type == "click" and event.product_id:
        product_key = f"telemetry:{tenant.organization_id}:trending_products:7d"
        background_tasks.add_task(
            cache.zincrby,
            key=product_key,
            amount=1.0,
            member=event.product_id
        )
        
    if event.query:
        query_key = f"telemetry:{tenant.organization_id}:trending_searches:7d"
        background_tasks.add_task(
            cache.zincrby,
            key=query_key,
            amount=1.0,
            member=event.query
        )
        
        # Also increment global trending queries as requested by SRE check
        background_tasks.add_task(
            cache.zincrby,
            key="trending:queries",
            amount=1.0,
            member=event.query
        )
        
    return BaseResponse(success=True, message="Event logged successfully")

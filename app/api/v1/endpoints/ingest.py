"""
Ingestion & Webhook API Endpoints
"""
import json
import uuid
from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request

from app.api.dependencies import get_tenant_context, TenantContext, require_admin_key, check_rate_limit
from app.container import Container, get_container
from app.infrastructure.db.models import CatalogIntegration

router = APIRouter()
@router.post("/webhook/{source_id}")


async def receive_webhook(
    source_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    x_webhook_secret: str = Header(..., description="Unique immutable secret for this data source"),
):
    """
    Receive webhook payload, validate secret, publish to Redis Pub/Sub for live terminal, 
    and process in background.
    """
    container = get_container()
    db = container.get("db_session")
    redis = container.get("redis")
    
    if not db or not redis:
        raise HTTPException(status_code=503, detail="Services unavailable")
        
    client_ip = request.client.host if request.client else "unknown"
    if not await check_rate_limit(f"webhook:{source_id}:{client_ip}", limit=100, window=60, cache=redis):
        raise HTTPException(status_code=429, detail="Too many webhook requests from this IP")
        
    async with db() as session:
        # 1. Validate Secret against CatalogIntegration
        from sqlalchemy import select
        stmt = select(CatalogIntegration).where(
            CatalogIntegration.id == source_id,
            CatalogIntegration.config.op("->>")("webhook_secret") == x_webhook_secret
        )
        result = await session.execute(stmt)
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise HTTPException(status_code=401, detail="Invalid webhook secret or source ID")

        # 2. Get the raw payload
        try:
            payload = await request.json()
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # 3. Save a preview to the database for the UI Mapper (up to 10 items)
        preview_items = payload.get("products", [])[:10] if isinstance(payload, dict) else []
        current_config = dict(integration.config or {})
        current_config["last_payload_preview"] = preview_items
        integration.config = current_config
        await session.commit()

        # 4. Publish to Redis Pub/Sub for the Live Terminal UX (WebSocket)
        org_id = str(integration.organization_id)
        channel = f"tenant:{org_id}:logs"
        
        log_message = {
            "type": "webhook_received",
            "source_id": source_id,
            "payload_preview": preview_items
        }
        await redis.publish(channel, json.dumps(log_message))
        
        # 5. Process in background to index to Typesense
        from app.workers.catalog_worker import process_webhook_ingestion
        background_tasks.add_task(
            process_webhook_ingestion,
            org_id=org_id,
            source_id=source_id,
            payload=payload,
            container=container
        )
            
        return {"status": "accepted", "message": "Payload received and processing started"}


@router.post("/sources")
async def create_data_source(
    data: Dict[str, Any],
    tenant: TenantContext = Depends(require_admin_key)
):
    """
    Generate a new Webhook Source (Screen 1 of Hybrid Wizard)
    """
    container = get_container()
    db = container.get("db_session")
    
    async with db() as session:
        webhook_secret = f"whsec_{uuid.uuid4().hex}"
        
        new_source = CatalogIntegration(
            organization_id=tenant.organization_id,
            integration_type="webhook",
            config={
                "webhook_secret": webhook_secret,
                "field_mapping": {}
            },
            sync_status="pending"
        )
        session.add(new_source)
        await session.commit()
        await session.refresh(new_source)
        
        return {
            "source_id": str(new_source.id),
            "webhook_endpoint": f"/api/v1/ingest/webhook/{new_source.id}",
            "webhook_secret": webhook_secret
        }

@router.put("/sources/{source_id}/mapping")
async def update_source_mapping(
    source_id: str,
    field_mapping: Dict[str, str],
    tenant: TenantContext = Depends(require_admin_key)
):
    """
    Update the field mapping for a specific webhook source.
    """
    container = get_container()
    db = container.get("db_session")
    
    async with db() as session:
        from sqlalchemy import select, update
        
        stmt = select(CatalogIntegration).where(
            CatalogIntegration.id == source_id,
            CatalogIntegration.organization_id == tenant.organization_id
        )
        result = await session.execute(stmt)
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Source not found")
            
        # Update config mapping
        current_config = dict(integration.config or {})
        current_config["field_mapping"] = field_mapping
        
        integration.config = current_config
        
        await session.commit()
        return {"status": "success", "field_mapping": field_mapping}

@router.get("/sources/{source_id}")
async def get_source(
    source_id: str,
    tenant: TenantContext = Depends(require_admin_key)
):
    """
    Get the details of a webhook source, including the latest payload preview.
    """
    container = get_container()
    db = container.get("db_session")
    
    async with db() as session:
        from sqlalchemy import select
        
        stmt = select(CatalogIntegration).where(
            CatalogIntegration.id == source_id,
            CatalogIntegration.organization_id == tenant.organization_id
        )
        result = await session.execute(stmt)
        integration = result.scalar_one_or_none()
        
        if not integration:
            raise HTTPException(status_code=404, detail="Source not found")
            
        return {
            "id": str(integration.id),
            "type": integration.integration_type,
            "status": integration.sync_status,
            "config": integration.config,
            "created_at": integration.created_at
        }

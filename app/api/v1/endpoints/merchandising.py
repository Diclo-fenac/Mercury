"""
Merchandising Rules API Endpoints
"""
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.dependencies import TenantContext, get_container_dependency, require_admin_key
from app.infrastructure.db.models import MerchandisingRule

router = APIRouter()

class MerchandisingRuleSchema(BaseModel):
    query_exact_match: str
    pinned_items: List[str]
    hidden_items: List[str]

@router.get("/")
async def list_rules(
    ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """List all merchandising rules for the organization"""
    db = container.get("db_session")
    if not db:
        raise HTTPException(status_code=503, detail="Database unavailable")
        
    async with db() as session:
        from sqlalchemy import select
        stmt = select(MerchandisingRule).where(
            MerchandisingRule.organization_id == uuid.UUID(ctx.organization_id)
        )
        res = await session.execute(stmt)
        rules = res.scalars().all()
        
        return {
            "success": True,
            "rules": [
                {
                    "id": str(r.id),
                    "query_exact_match": r.query_exact_match,
                    "pinned_items": r.pinned_items,
                    "hidden_items": r.hidden_items,
                    "is_active": r.is_active
                }
                for r in rules
            ]
        }

@router.post("/")
async def upsert_rule(
    rule: MerchandisingRuleSchema,
    ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Create or update a merchandising rule (pin/hide)"""
    db = container.get("db_session")
    async with db() as session:
        from sqlalchemy import select
        org_uuid = uuid.UUID(ctx.organization_id)
        
        stmt = select(MerchandisingRule).where(
            MerchandisingRule.organization_id == org_uuid,
            MerchandisingRule.query_exact_match == rule.query_exact_match.lower()
        )
        res = await session.execute(stmt)
        existing = res.scalar_one_or_none()
        
        if existing:
            existing.pinned_items = rule.pinned_items
            existing.hidden_items = rule.hidden_items
            existing.is_active = True
        else:
            new_rule = MerchandisingRule(
                organization_id=org_uuid,
                query_exact_match=rule.query_exact_match.lower(),
                pinned_items=rule.pinned_items,
                hidden_items=rule.hidden_items
            )
            session.add(new_rule)
            
        await session.commit()
        
        # Invalidate search cache
        cache = container.get("redis")
        if cache:
            await cache.bump_tenant_namespace_revision(ctx.organization_id, "search")
            
        return {"success": True, "message": "Merchandising rule saved"}

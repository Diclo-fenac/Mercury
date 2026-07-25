"""
Admin Endpoints for Merchant Onboarding, Keys, Custom Rules, Configs, and Analytics
"""
import logging
import uuid
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

from app.api.dependencies import (
    TenantContext,
    get_container_dependency,
    require_admin_key,
    require_scope,
)

router = APIRouter()


class OnboardRequest(BaseModel):
    name: str = Field(..., description="Organization/Store Name")
    slug: str = Field(..., description="Unique URL friendly identifier")
    owner_email: str = Field(..., description="Owner email address")
    plan: str = Field(default="free", description="Pricing plan: free, pro, enterprise")


class KeyGenRequest(BaseModel):
    key_type: str = Field(..., description="Key type: public_search or private_admin")
    name: str = Field(..., description="Name/Label for the key")
    scopes: List[str] = Field(default=["search"], description="Allowed scopes")


class SynonymRequest(BaseModel):
    term: str = Field(..., description="Term to expand")
    synonyms: List[str] = Field(..., description="List of synonym terms")


class PinnedProductRequest(BaseModel):
    query_pattern: str = Field(..., description="Query phrase or pattern")
    product_id: str = Field(..., description="Product ID to pin")
    position: int = Field(default=1, ge=1, description="1-indexed target position")


class ConfigUpdateRequest(BaseModel):
    enable_semantic: Optional[bool] = None
    enable_personalization: Optional[bool] = None
    enable_image_search: Optional[bool] = None
    rrf_keyword_weight: Optional[float] = None
    rrf_vector_weight: Optional[float] = None
    typo_tolerance: Optional[int] = None
    searchable_fields: Optional[List[str]] = None
    facet_fields: Optional[List[str]] = None
    widget_primary_color: Optional[str] = None
    widget_font_family: Optional[str] = None
    widget_position: Optional[str] = None
    widget_placeholder: Optional[str] = None
    out_of_stock_behavior: Optional[str] = None
    allowed_domains: Optional[List[str]] = None


@router.post("/onboard", status_code=status.HTTP_201_CREATED)
async def onboard_tenant(
    request: OnboardRequest,
    response: Response,
    req: Request,
    container = Depends(get_container_dependency)
):
    """Onboard a new merchant organization, provision its Typesense index, and generate initial keys."""
    tenant_service = container.get("tenant_service")
    tenant_provisioner = container.get("tenant_provisioner")

    if not tenant_service or not tenant_provisioner:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-tenancy provisioning services not available"
        )
        
    client_ip = req.client.host if req.client else "unknown"
    cache = container.get("redis")
    from app.api.dependencies import check_rate_limit
    # Strict rate limit for onboarding: 5 per hour per IP
    if not await check_rate_limit(f"onboard:{client_ip}", limit=5, window=3600, cache=cache):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many onboarding requests from this IP"
        )

    try:
        # 1. Create Organization & defaults
        org = await tenant_service.create_organization(
            name=request.name,
            slug=request.slug,
            owner_email=request.owner_email,
            plan=request.plan
        )
        org_id = org["id"]

        # 2. Provision Typesense collection (default dimension 384)
        provision_ok = await tenant_provisioner.provision_tenant(org_id, num_dim=384)
        if not provision_ok:
            raise Exception("Failed to provision Typesense collection")

        # 3. Generate initial private admin key (sk_*)
        _, admin_key = await tenant_service.generate_api_key(
            org_id=org_id,
            key_type="private_admin",
            name="Default Admin Key",
            scopes=["admin", "all", "*"]
        )

        # 4. Generate initial public search key (pk_*)
        _, search_key = await tenant_service.generate_api_key(
            org_id=org_id,
            key_type="public_search",
            name="Default Search Key",
            scopes=["search"]
        )

        res_body = {
            "success": True,
            "organization": {
                "id": org_id,
                "name": org["name"],
                "slug": org["slug"],
                "plan": org["plan"]
            },
            "keys": {
                "admin_key": admin_key,
                "search_key": search_key
            }
        }

        response.set_cookie(
            key="admin_token",
            value=admin_key,
            httponly=True,
            samesite="lax",
            secure=False,
            max_age=30 * 24 * 60 * 60
        )
        return res_body
    except Exception as e:
        logger.error(f"Onboarding failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Onboarding failed due to an internal server error"
        )


class LoginRequest(BaseModel):
    admin_key: str = Field(..., description="Private admin key (sk_*)")

@router.post("/login", status_code=status.HTTP_200_OK)
async def login_tenant(
    request: LoginRequest,
    response: Response,
    req: Request,
    container = Depends(get_container_dependency)
):
    """Authenticate and set session cookie"""
    client_ip = req.client.host if req.client else "unknown"
    cache = container.get("redis")
    from app.api.dependencies import check_rate_limit
    # Rate limit: 10 attempts per minute per IP
    if not await check_rate_limit(f"login:{client_ip}", limit=10, window=60, cache=cache):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts"
        )
        
    tenant_service = container.get("tenant_service")
    ctx_dict = await tenant_service.validate_api_key(request.admin_key)
    if not ctx_dict or ctx_dict.get("key_type") != "private_admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin key"
        )
        
    response.set_cookie(
        key="admin_token",
        value=request.admin_key,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=30 * 24 * 60 * 60
    )
    
    return {"status": "ok", "organization_id": ctx_dict.get("organization_id")}

@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_tenant(response: Response):
    """Clear session cookie"""
    response.delete_cookie(
        key="admin_token",
        httponly=True,
        samesite="lax",
        secure=False
    )
    return {"status": "ok"}

@router.get("/verify", status_code=status.HTTP_200_OK)
async def verify_tenant(ctx: TenantContext = Depends(require_admin_key)):
    """Verify session cookie is still valid"""
    return {"status": "ok", "organization_id": ctx.organization_id}


@router.post("/keys")
async def generate_api_key(
    request: KeyGenRequest,
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Generate a new API key for the tenant."""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant service not available"
        )

    try:
        prefix, raw_key = await tenant_service.generate_api_key(
            org_id=tenant_ctx.organization_id,
            key_type=request.key_type,
            name=request.name,
            scopes=request.scopes
        )
        return {
            "success": True,
            "key_prefix": prefix,
            "api_key": raw_key
        }
    except Exception as e:
        logger.error(f"Key generation failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Key generation failed due to an internal server error"
        )

@router.get("/keys")
async def list_api_keys(
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """List API keys for the tenant."""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant service not available"
        )
    return await tenant_service.get_api_keys(tenant_ctx.organization_id)


@router.get("/config")
async def get_tenant_config(
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Get the current search config for the tenant."""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant service not available"
        )

    config = await tenant_service.get_config(tenant_ctx.organization_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Configuration not found"
        )
    return config


@router.patch("/config")
async def update_tenant_config(
    request: ConfigUpdateRequest,
    tenant_ctx: TenantContext = Depends(require_scope("settings:write")),
    container = Depends(get_container_dependency)
):
    """Update tenant configuration."""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant service not available"
        )

    # Filter out None values to perform partial updates
    updates = {k: v for k, v in request.model_dump().items() if v is not None}
    if not updates:
        return {"success": True, "message": "No updates provided"}

    try:
        ok = await tenant_service.update_config(tenant_ctx.organization_id, **updates)
        return {"success": ok}
    except Exception as e:
        logger.error(f"Config update failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Config update failed due to an internal server error"
        )


@router.post("/synonyms")
async def add_synonym(
    request: SynonymRequest,
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Add a synonym expansion rule."""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant service not available"
        )

    try:
        from app.domain.tenants.models import Synonym
        async with tenant_service.db.async_session() as session:
            syn = Synonym(
                organization_id=uuid.UUID(tenant_ctx.organization_id),
                term=request.term.lower(),
                synonyms=[s.lower() for s in request.synonyms],
                is_active=True
            )
            session.add(syn)
            await session.commit()

        await tenant_service.update_config(tenant_ctx.organization_id, has_merchandising_rules=True)

        typesense_client = container.get("typesense")
        if typesense_client:
            collection_name = f"tenant_{tenant_ctx.organization_id}_products"
            synonym_id = f"syn_{request.term.replace(' ', '_')}"
            await typesense_client.upsert_synonym(
                collection_name,
                synonym_id,
                [s.lower() for s in request.synonyms],
                root=request.term.lower()
            )

        return {"success": True}
    except Exception as e:
        logger.error(f"Add synonym failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Add synonym failed due to an internal server error"
        )


@router.post("/pinned")
async def add_pinned_product(
    request: PinnedProductRequest,
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Pin a product to a specific query position."""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant service not available"
        )

    try:
        from app.domain.tenants.models import PinnedProduct
        async with tenant_service.db.async_session() as session:
            pin = PinnedProduct(
                organization_id=uuid.UUID(tenant_ctx.organization_id),
                query_pattern=request.query_pattern.lower(),
                product_id=request.product_id,
                position=request.position,
                is_active=True
            )
            session.add(pin)
            await session.commit()
        await tenant_service.update_config(tenant_ctx.organization_id, has_merchandising_rules=True)
        return {"success": True}
    except Exception as e:
        logger.error(f"Add pinned product failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Add pinned product failed due to an internal server error"
        )

@router.get("/pinned")
async def get_pinned_products(
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Get all pinned products for the tenant."""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant service not available"
        )

    try:
        from sqlalchemy import select

        from app.domain.tenants.models import PinnedProduct
        async with tenant_service.db.async_session() as session:
            stmt = select(PinnedProduct).where(PinnedProduct.organization_id == uuid.UUID(tenant_ctx.organization_id))
            result = await session.execute(stmt)
            pins = result.scalars().all()
            
            return [
                {
                    "id": str(pin.id),
                    "query_pattern": pin.query_pattern,
                    "product_id": pin.product_id,
                    "position": pin.position,
                    "is_active": pin.is_active
                }
                for pin in pins
            ]
    except Exception as e:
        logger.error(f"Get pinned products failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get pinned products failed due to an internal server error"
        )

@router.get("/analytics")
async def get_tenant_analytics(
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Get usage reports and top query patterns."""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Tenant service not available"
        )

    try:
        analytics = await tenant_service.get_analytics(tenant_ctx.organization_id)
        return analytics
    except Exception as e:
        logger.error(f"Get analytics failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Get analytics failed due to an internal server error"
        )


@router.put("/catalog/sync")
async def sync_catalog(
    products: List[Dict[str, Any]],
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Bulk import products from JSON array, generate embeddings, and index into Typesense."""
    catalog_importer = container.get("catalog_importer")
    if not catalog_importer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog importer service not available"
        )

    try:
        stats = await catalog_importer.import_json(tenant_ctx.organization_id, products, async_mode=True)
        tenant_service = container.get("tenant_service")
        if tenant_service:
            await tenant_service.update_config(tenant_ctx.organization_id, has_ingested_catalog=True)
        return {
            "success": stats.get("success", False),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Sync failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Catalog sync failed due to an internal server error"
        )

@router.post("/catalog/upload")
async def upload_csv_catalog(
    file: UploadFile = File(...),
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Bulk import products from a CSV file (for drag-and-drop dashboard UI)."""
    catalog_importer = container.get("catalog_importer")
    if not catalog_importer:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog importer service not available"
        )

    filename = file.filename or ""
    if not filename.endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    try:
        content_bytes = await file.read()
        csv_content = content_bytes.decode("utf-8", errors="ignore")

        stats = await catalog_importer.import_csv(tenant_ctx.organization_id, csv_content, async_mode=True)
        tenant_service = container.get("tenant_service")
        if tenant_service:
            await tenant_service.update_config(tenant_ctx.organization_id, has_ingested_catalog=True)
        return {
            "success": stats.get("success", False),
            "stats": stats
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Catalog upload failed due to an internal server error"
        )


@router.get("/catalog/stats")
async def get_catalog_stats(
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Retrieve indexing stats for the tenant's collection (e.g., product count)."""
    typesense_client = container.get("typesense")
    if not typesense_client or not typesense_client._connected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Typesense service not connected"
        )

    collection_name = f"tenant_{tenant_ctx.organization_id}_products"
    try:
        exists = await typesense_client.collection_exists(collection_name)
        if not exists:
            return {
                "exists": False,
                "product_count": 0,
                "collection_name": collection_name
            }

        loop = typesense_client.client.collections[collection_name].documents.search
        import asyncio
        res = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: loop({"q": "*", "per_page": 0})
        )
        found = res.get("found", 0)

        return {
            "exists": True,
            "product_count": found,
            "collection_name": collection_name
        }
    except Exception as e:
        logger.error(f"Failed to fetch catalog stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch catalog stats due to an internal server error"
        )


@router.post("/catalog/products")
@router.put("/catalog/products/{product_id}")
async def upsert_product(
    product: Dict[str, Any],
    product_id: Optional[str] = None,
    tenant_ctx: TenantContext = Depends(require_scope("catalog:write")),
    container = Depends(get_container_dependency)
):
    """Upsert canonical product; durable worker updates derived Typesense index."""
    catalog_service = container.get("catalog_service")
    if not catalog_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog service unavailable",
        )

    prod_id = product_id or str(product.get("id", ""))
    if not prod_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product ID is required either in URL or body"
        )

    try:
        title = product.get("title") or product.get("name") or ""
        name = product.get("name") or product.get("title") or ""
        description = product.get("description") or ""
        brand = product.get("brand") or "Unknown"
        category = product.get("category") or "General"
        sub_category = product.get("sub_category") or ""

        try:
            price_val = product.get("selling_price") or product.get("price") or 0.0
            selling_price = float(price_val)
        except (ValueError, TypeError):
            selling_price = 0.0

        try:
            rating_val = product.get("rating") or 0.0
            rating = float(rating_val)
        except (ValueError, TypeError):
            rating = 0.0

        stock = bool(product.get("stock", True))
        online_available = bool(product.get("online_available", True))

        doc = {
            "id": prod_id,
            "name": name,
            "title": title,
            "brand": brand,
            "category": category,
            "sub_category": sub_category,
            "description": description,
            "rating": rating,
            "stock": stock,
            "online_available": online_available,
            "selling_price": selling_price,
        }

        persisted = await catalog_service.upsert_products(tenant_ctx.organization_id, [doc])
        tenant_service = container.get("tenant_service")
        if tenant_service:
            await tenant_service.update_config(tenant_ctx.organization_id, has_ingested_catalog=True)
        worker = container.get("catalog_index_worker")
        if worker:
            await worker.run_once(limit=10)
        return {
            "success": True,
            "action": "upsert",
            "id": prod_id,
            "index_status": "indexed" if worker else "pending",
            "index_event_id": persisted[0]["index_event_id"],
        }

    except Exception as e:
        logger.error(f"Upsert failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Upsert failed due to an internal server error"
        )

@router.delete("/catalog/products/{product_id}")
async def delete_product(
    product_id: str,
    tenant_ctx: TenantContext = Depends(require_scope("catalog:write")),
    container = Depends(get_container_dependency)
):
    """Delete canonical product; worker removes derived search document."""
    catalog_service = container.get("catalog_service")
    if not catalog_service:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Catalog service unavailable",
        )

    try:
        deleted = await catalog_service.delete_product(tenant_ctx.organization_id, product_id)
        worker = container.get("catalog_index_worker")
        if worker and deleted:
            await worker.run_once(limit=10)
        return {
            "success": True,
            "action": "delete",
            "id": product_id,
            "note": None if deleted else "not found",
        }
    except Exception as e:
        logger.error(f"Delete failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Delete failed due to an internal server error"
        )


@router.post("/catalog/webhook")
async def catalog_webhook(
    payload: Dict[str, Any],
    tenant_ctx: TenantContext = Depends(require_scope("catalog:write")),
    container = Depends(get_container_dependency)
):
    """Handle webhook upsert/delete for catalog items."""
    action = payload.get("action", "").lower()
    product = payload.get("product", {})
    if action == "upsert":
        return await upsert_product(product=product, tenant_ctx=tenant_ctx, container=container)
    elif action == "delete":
        prod_id = product.get("id")
        if not prod_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product ID required for delete")
        return await delete_product(product_id=str(prod_id), tenant_ctx=tenant_ctx, container=container)
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unsupported action: {action}")


@router.get("/webhooks")
async def get_webhooks(
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Get webhook endpoints"""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(status_code=500, detail="Service unavailable")

    config = await tenant_service.get_config(tenant_ctx.organization_id)
    return {"webhook_urls": config.get("webhook_urls", []) if config else []}


@router.post("/webhooks")
async def update_webhooks(
    payload: Dict[str, Any],
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Update webhook endpoints"""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(status_code=500, detail="Service unavailable")

    urls = payload.get("webhook_urls", [])
    await tenant_service.update_config(tenant_ctx.organization_id, webhook_urls=urls)
    return {"success": True, "webhook_urls": urls}


@router.get("/rules/synonyms")
async def get_all_synonyms(
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Get all synonyms"""
    tenant_service = container.get("tenant_service")
    if not tenant_service:
        raise HTTPException(status_code=500, detail="Service unavailable")

    synonyms = await tenant_service.get_all_synonyms(tenant_ctx.organization_id)
    return {"synonyms": synonyms}


@router.post("/rules/synonyms")
async def create_synonym(
    payload: Dict[str, Any],
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Add a synonym rule"""
    tenant_service = container.get("tenant_service")
    typesense_client = container.get("typesense")
    if not tenant_service:
        raise HTTPException(status_code=500, detail="Service unavailable")

    term = payload.get("term")
    synonyms = payload.get("synonyms", [])
    if not term or not synonyms:
        raise HTTPException(status_code=400, detail="term and synonyms required")

    await tenant_service.add_synonym(tenant_ctx.organization_id, term, synonyms)

    # Push to Typesense natively
    collection_name = f"tenant_{tenant_ctx.organization_id}_products"
    synonym_id = f"syn_{term.replace(' ', '_')}"
    # Bidirectional if root is empty, otherwise one-way
    # To map "mobile" -> "smartphone", root="mobile", synonyms=["smartphone"]
    typesense_synced = False
    if typesense_client:
        typesense_synced = await typesense_client.upsert_synonym(
            collection_name, synonym_id, synonyms, root=term
        )

    return {"success": True, "typesense_synced": typesense_synced}


@router.delete("/rules/synonyms/{term}")
async def delete_synonym(
    term: str,
    tenant_ctx: TenantContext = Depends(require_admin_key),
    container = Depends(get_container_dependency)
):
    """Delete a synonym rule"""
    tenant_service = container.get("tenant_service")
    typesense_client = container.get("typesense")
    if not tenant_service:
        raise HTTPException(status_code=500, detail="Service unavailable")

    await tenant_service.remove_synonym(tenant_ctx.organization_id, term)

    if typesense_client:
        collection_name = f"tenant_{tenant_ctx.organization_id}_products"
        synonym_id = f"syn_{term.replace(' ', '_')}"
        await typesense_client.delete_synonym(collection_name, synonym_id)

    return {"success": True}

@router.get("/system/metrics")
async def get_system_metrics(
    tenant_ctx: TenantContext = Depends(require_admin_key)
):
    """Get live system resources"""
    import psutil
    try:
        import torch
        gpu_enabled = torch.cuda.is_available()
        gpu_name = torch.cuda.get_device_name(0) if gpu_enabled else "N/A"
    except ImportError:
        gpu_enabled = False
        gpu_name = "N/A"

    return {
        "cpu_percent": psutil.cpu_percent(interval=0.1),
        "ram_percent": psutil.virtual_memory().percent,
        "gpu_enabled": gpu_enabled,
        "gpu_name": gpu_name
    }

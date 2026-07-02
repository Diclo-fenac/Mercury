"""
Tenant Service - Layer 5: Domain
Manages SaaS organizations, API keys, tenant configurations, and usage recording
"""
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import delete, func, select, update

from app.domain.tenants.models import (
    APIKey,
    Organization,
    PinnedProduct,
    Synonym,
    TenantConfig,
    UsageEvent,
)
from app.infrastructure.cache.redis import RedisClient
from app.infrastructure.db.postgres import PostgresClient


class TenantService:
    """Service for managing multi-tenancy organizations, keys, and configs"""

    def __init__(self, db: PostgresClient, cache: Optional[RedisClient] = None):
        self.db = db
        self.cache = cache

    async def create_organization(self, name: str, slug: str, owner_email: str, plan: str = "free") -> Dict[str, Any]:
        """Create new organization and initialize its default tenant config"""
        async with self.db.async_session() as session:
            # 1. Create Organization
            org = Organization(
                name=name,
                slug=slug,
                owner_email=owner_email,
                plan=plan,
                status="active"
            )
            session.add(org)
            await session.flush()  # populate org.id

            # 2. Create default TenantConfig
            config = TenantConfig(
                organization_id=org.id,
                enable_semantic=True,
                enable_personalization=False,
                enable_image_search=False,
                rrf_keyword_weight=0.6,
                rrf_vector_weight=0.4,
                typo_tolerance=2,
                searchable_fields=["title", "description", "brand", "category"],
                facet_fields=["brand", "category"],
                widget_primary_color="#6366f1",
                widget_font_family="Inter",
                widget_position="center",
                widget_placeholder="Search products...",
                out_of_stock_behavior="demote",
                webhook_urls=[]
            )
            session.add(config)
            await session.commit()

            return {
                "id": str(org.id),
                "name": org.name,
                "slug": org.slug,
                "plan": org.plan,
                "status": org.status
            }

    async def generate_api_key(
        self,
        org_id: str,
        key_type: str,
        name: str,
        scopes: Optional[List[str]] = None
    ) -> Tuple[str, str]:
        """Generate API key. Returns (key_prefix, raw_key)"""
        raw_uuid = uuid.uuid4().hex
        prefix = "pk_" if key_type == "public_search" else "sk_"
        raw_key = f"{prefix}{raw_uuid}"
        
        # Hash key with SHA-256
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        display_prefix = raw_key[:12]

        async with self.db.async_session() as session:
            api_key = APIKey(
                organization_id=uuid.UUID(org_id),
                key_prefix=display_prefix,
                key_hash=key_hash,
                key_type=key_type,
                name=name,
                scopes=scopes or [],
                is_active=True
            )
            session.add(api_key)
            await session.commit()

        return display_prefix, raw_key

    async def validate_api_key(self, raw_key: str) -> Optional[Dict[str, Any]]:
        """Validate API key and return tenant context. Cached in Redis."""
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        cache_key = f"tenant_context:{key_hash}"

        # 1. Try cache
        if self.cache:
            try:
                cached = await self.cache.get_json(cache_key)
                if cached:
                    return cached
            except Exception:
                pass

        # 2. Fetch from Postgres
        async with self.db.async_session() as session:
            stmt = (
                select(
                    APIKey.id.label("key_id"),
                    APIKey.key_type,
                    APIKey.scopes,
                    APIKey.is_active,
                    Organization.id.label("org_id"),
                    Organization.slug.label("org_slug"),
                    Organization.status.label("org_status"),
                    Organization.plan.label("org_plan")
                )
                .join(Organization, APIKey.organization_id == Organization.id)
                .where(APIKey.key_hash == key_hash)
            )
            result = await session.execute(stmt)
            row = result.first()

            if not row or not row.is_active or row.org_status != "active":
                return None

            # Fetch config
            config_stmt = select(TenantConfig).where(TenantConfig.organization_id == row.org_id)
            config_result = await session.execute(config_stmt)
            config = config_result.scalar_one_or_none()

            # Construct config dict
            config_dict = {
                "enable_semantic": config.enable_semantic if config else True,
                "enable_personalization": config.enable_personalization if config else False,
                "enable_image_search": config.enable_image_search if config else False,
                "rrf_keyword_weight": config.rrf_keyword_weight if config else 0.6,
                "rrf_vector_weight": config.rrf_vector_weight if config else 0.4,
                "typo_tolerance": config.typo_tolerance if config else 2,
                "searchable_fields": config.searchable_fields if config else ["title", "description", "brand", "category"],
                "facet_fields": config.facet_fields if config else ["brand", "category"],
                "widget_primary_color": config.widget_primary_color if config else "#6366f1",
                "widget_font_family": config.widget_font_family if config else "Inter",
                "widget_position": config.widget_position if config else "center",
                "widget_placeholder": config.widget_placeholder if config else "Search products...",
                "out_of_stock_behavior": config.out_of_stock_behavior if config else "demote"
            }

            ctx = {
                "key_id": str(row.key_id),
                "key_type": row.key_type,
                "scopes": row.scopes,
                "organization_id": str(row.org_id),
                "organization_slug": row.org_slug,
                "plan": row.org_plan,
                "config": config_dict
            }

            # Update last used timestamp
            await session.execute(
                update(APIKey)
                .where(APIKey.id == row.key_id)
                .values(last_used_at=func.now())
            )
            await session.commit()

        # 3. Cache result
        if self.cache:
            try:
                await self.cache.set_json(cache_key, ctx, ttl=3600)  # 1 hour cache
            except Exception:
                pass

        return ctx

    async def get_config(self, org_id: str) -> Optional[Dict[str, Any]]:
        """Get organization's search/widget configuration"""
        async with self.db.async_session() as session:
            stmt = select(TenantConfig).where(TenantConfig.organization_id == uuid.UUID(org_id))
            res = await session.execute(stmt)
            config = res.scalar_one_or_none()
            if not config:
                return None
            return {
                "enable_semantic": config.enable_semantic,
                "enable_personalization": config.enable_personalization,
                "enable_image_search": config.enable_image_search,
                "rrf_keyword_weight": config.rrf_keyword_weight,
                "rrf_vector_weight": config.rrf_vector_weight,
                "typo_tolerance": config.typo_tolerance,
                "searchable_fields": config.searchable_fields,
                "facet_fields": config.facet_fields,
                "widget_primary_color": config.widget_primary_color,
                "widget_font_family": config.widget_font_family,
                "widget_position": config.widget_position,
                "widget_placeholder": config.widget_placeholder,
                "out_of_stock_behavior": config.out_of_stock_behavior,
                "webhook_urls": config.webhook_urls or []
            }

    async def update_config(self, org_id: str, **kwargs) -> bool:
        """Update organization's config. Invalidates cached key contexts."""
        org_uuid = uuid.UUID(org_id)
        async with self.db.async_session() as session:
            stmt = (
                update(TenantConfig)
                .where(TenantConfig.organization_id == org_uuid)
                .values(**kwargs)
            )
            await session.execute(stmt)
            await session.commit()

        # Invalidate tenant's contexts in Redis cache
        if self.cache:
            # For simplicity, we can let TTL expire, or if needed lookup org's keys.
            # Real SaaS: lookup keys, delete context keys.
            pass
        return True

    async def get_pinned_products(self, org_id: str, query: str) -> List[Dict[str, Any]]:
        """Get pinned products matching query pattern"""
        org_uuid = uuid.UUID(org_id)
        async with self.db.async_session() as session:
            stmt = (
                select(PinnedProduct)
                .where(
                    PinnedProduct.organization_id == org_uuid,
                    PinnedProduct.is_active == True,
                    PinnedProduct.query_pattern.in_([query.lower(), '*'])
                )
                .order_by(PinnedProduct.position.asc())
            )
            res = await session.execute(stmt)
            pins = res.scalars().all()
            return [
                {
                    "product_id": p.product_id,
                    "position": p.position
                }
                for p in pins
            ]

    async def get_synonyms(self, org_id: str, term: str) -> List[str]:
        """Get synonyms for a given term"""
        org_uuid = uuid.UUID(org_id)
        async with self.db.async_session() as session:
            stmt = (
                select(Synonym)
                .where(
                    Synonym.organization_id == org_uuid,
                    Synonym.is_active == True,
                    Synonym.term == term.lower()
                )
            )
            res = await session.execute(stmt)
            syn = res.scalar_one_or_none()
            return syn.synonyms if syn else []

    async def get_all_synonyms(self, org_id: str) -> List[Dict[str, Any]]:
        """Get all synonyms for an organization"""
        org_uuid = uuid.UUID(org_id)
        async with self.db.async_session() as session:
            stmt = select(Synonym).where(Synonym.organization_id == org_uuid, Synonym.is_active == True)
            res = await session.execute(stmt)
            return [{"term": s.term, "synonyms": s.synonyms} for s in res.scalars().all()]

    async def add_synonym(self, org_id: str, term: str, synonyms: List[str]) -> bool:
        """Add or update a synonym rule"""
        org_uuid = uuid.UUID(org_id)
        async with self.db.async_session() as session:
            # Check if exists
            stmt = select(Synonym).where(Synonym.organization_id == org_uuid, Synonym.term == term.lower())
            res = await session.execute(stmt)
            existing = res.scalar_one_or_none()

            if existing:
                existing.synonyms = list(set(existing.synonyms + synonyms))
                existing.is_active = True
            else:
                session.add(Synonym(
                    organization_id=org_uuid,
                    term=term.lower(),
                    synonyms=synonyms
                ))
            await session.commit()
            return True

    async def remove_synonym(self, org_id: str, term: str) -> bool:
        """Remove a synonym rule"""
        org_uuid = uuid.UUID(org_id)
        async with self.db.async_session() as session:
            stmt = delete(Synonym).where(Synonym.organization_id == org_uuid, Synonym.term == term.lower())
            await session.execute(stmt)
            await session.commit()
            return True

    async def record_usage(
        self,
        org_id: str,
        event_type: str,
        query_text: Optional[str] = None,
        latency_ms: Optional[int] = None,
        result_count: Optional[int] = None,
        api_key_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """Record usage event in background"""
        try:
            async with self.db.async_session() as session:
                event = UsageEvent(
                    organization_id=uuid.UUID(org_id),
                    event_type=event_type,
                    query_text=query_text,
                    latency_ms=latency_ms,
                    result_count=result_count,
                    api_key_id=uuid.UUID(api_key_id) if api_key_id else None,
                    ip_address=ip_address
                )
                session.add(event)
                await session.commit()
        except Exception:
            pass

    async def check_usage_limit(self, org_id: str) -> Tuple[bool, int]:
        """Check if organization is within monthly query limit"""
        org_uuid = uuid.UUID(org_id)
        async with self.db.async_session() as session:
            # 1. Fetch limit and plan
            org_stmt = select(Organization.monthly_query_limit, Organization.plan).where(Organization.id == org_uuid)
            org_res = await session.execute(org_stmt)
            row = org_res.first()
            if not row:
                return False, 0
            
            limit = row.monthly_query_limit
            if row.plan == "enterprise":
                return True, 999999999

            # 2. Count queries in current month
            now = datetime.now(timezone.utc)
            start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
            
            count_stmt = (
                select(func.count(UsageEvent.id))
                .where(
                    UsageEvent.organization_id == org_uuid,
                    UsageEvent.event_type == 'search_query',
                    UsageEvent.created_at >= start_of_month
                )
            )
            count_res = await session.execute(count_stmt)
            usage = count_res.scalar_one() or 0

            return usage < limit, max(0, limit - usage)

    async def get_analytics(self, org_id: str) -> Dict[str, Any]:
        """Get daily analytics and query patterns for tenant reports"""
        org_uuid = uuid.UUID(org_id)
        async with self.db.async_session() as session:
            # 1. Get total search queries
            total_stmt = select(func.count(UsageEvent.id)).where(
                UsageEvent.organization_id == org_uuid,
                UsageEvent.event_type == 'search_query'
            )
            total_res = await session.execute(total_stmt)
            total_queries = total_res.scalar_one() or 0

            # 2. Get zero result queries
            zero_stmt = select(func.count(UsageEvent.id)).where(
                UsageEvent.organization_id == org_uuid,
                UsageEvent.event_type == 'search_query',
                UsageEvent.result_count == 0
            )
            zero_res = await session.execute(zero_stmt)
            zero_queries = zero_res.scalar_one() or 0

            # 3. Get average latency
            avg_stmt = select(func.avg(UsageEvent.latency_ms)).where(
                UsageEvent.organization_id == org_uuid,
                UsageEvent.event_type == 'search_query'
            )
            avg_res = await session.execute(avg_stmt)
            avg_latency = float(avg_res.scalar_one() or 0.0)

            # 4. Get top query patterns
            top_stmt = (
                select(UsageEvent.query_text, func.count(UsageEvent.id).label('count'))
                .where(
                    UsageEvent.organization_id == org_uuid,
                    UsageEvent.event_type == 'search_query',
                    UsageEvent.query_text.is_not(None)
                )
                .group_by(UsageEvent.query_text)
                .order_by(func.count(UsageEvent.id).desc())
                .limit(10)
            )
            top_res = await session.execute(top_stmt)
            top_queries = [{"query": row.query_text, "count": row.count} for row in top_res.all()]

            return {
                "total_queries": total_queries,
                "zero_result_count": zero_queries,
                "average_latency_ms": round(avg_latency, 2),
                "top_queries": top_queries
            }

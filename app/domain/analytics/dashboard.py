"""
Analytics Dashboard Service - Layer 5: Domain
Aggregates metrics for merchant reporting
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import desc, func, select

from app.infrastructure.db.models import TenantActivity, TenantConversation
from app.infrastructure.db.postgres import PostgresClient
from app.utils.logger import get_logger

logger = get_logger("dashboard_service")

class DashboardService:
    def __init__(self, db: PostgresClient):
        self.db = db

    async def get_dashboard_metrics(self, organization_id: str, days: int = 30) -> Dict[str, Any]:
        """Get aggregate metrics for the dashboard"""
        try:
            # Parse organization_id string to UUID if needed, SQLAlchemy handles it mostly, 
            # but to be safe:
            org_uuid = uuid.UUID(organization_id) if isinstance(organization_id, str) else organization_id
            cutoff_date = datetime.utcnow() - timedelta(days=days)

            async with self.db.session() as session:
                # 1. Total Searches
                searches_query = select(func.count()).where(
                    TenantActivity.organization_id == org_uuid,
                    TenantActivity.activity_type == 'search',
                    TenantActivity.created_at >= cutoff_date
                )
                total_searches_result = await session.execute(searches_query)
                total_searches = total_searches_result.scalar() or 0

                # 2. Total Conversations
                conv_query = select(func.count()).where(
                    TenantConversation.organization_id == org_uuid,
                    TenantConversation.created_at >= cutoff_date
                )
                total_conv_result = await session.execute(conv_query)
                total_conversations = total_conv_result.scalar() or 0

                # 3. Top Searches (Top Queries)
                # Using jsonb_extract_path_text to get the 'query' field out of the data JSONB column
                top_searches_query = select(
                    func.jsonb_extract_path_text(TenantActivity.data, 'query').label('query'),
                    func.count().label('count')
                ).where(
                    TenantActivity.organization_id == org_uuid,
                    TenantActivity.activity_type == 'search',
                    TenantActivity.created_at >= cutoff_date,
                    TenantActivity.data.op('?')('query')
                ).group_by(
                    func.jsonb_extract_path_text(TenantActivity.data, 'query')
                ).order_by(
                    desc('count')
                ).limit(5)
                
                top_searches_result = await session.execute(top_searches_query)
                top_searches = [
                    {"query": row.query, "count": row.count} 
                    for row in top_searches_result.all() if row.query
                ]

                # 4. Top Products Viewed (activity_type == 'view')
                top_products_query = select(
                    func.jsonb_extract_path_text(TenantActivity.data, 'product_id').label('product_id'),
                    func.jsonb_extract_path_text(TenantActivity.data, 'product_name').label('name'),
                    func.count().label('count')
                ).where(
                    TenantActivity.organization_id == org_uuid,
                    TenantActivity.activity_type == 'view',
                    TenantActivity.created_at >= cutoff_date,
                    TenantActivity.data.op('?')('product_id')
                ).group_by(
                    func.jsonb_extract_path_text(TenantActivity.data, 'product_id'),
                    func.jsonb_extract_path_text(TenantActivity.data, 'product_name')
                ).order_by(
                    desc('count')
                ).limit(5)

                top_products_result = await session.execute(top_products_query)
                top_products_viewed = [
                    {"id": row.product_id, "name": row.name or "Unknown", "views": row.count}
                    for row in top_products_result.all()
                ]

                # 5. Conversion Rate (Rough proxy: distinct purchasers / distinct searchers)
                # For now, placeholder or 0 if no purchases
                conversion_rate = 0.0

            return {
                "organization_id": str(organization_id),
                "period_days": days,
                "total_searches": total_searches,
                "total_conversations": total_conversations,
                "conversion_rate": conversion_rate,
                "top_searches": top_searches,
                "top_products_viewed": top_products_viewed
            }
        except Exception as e:
            logger.error(f"Error fetching dashboard metrics: {e}")
            # Fallback to empty state structure so UI doesn't crash on type errors
            return {
                "organization_id": str(organization_id),
                "period_days": days,
                "total_searches": 0,
                "total_conversations": 0,
                "conversion_rate": 0,
                "top_searches": [],
                "top_products_viewed": []
            }

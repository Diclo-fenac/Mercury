"""
Audit Service
Layer 5: Domain Services - Enterprise Identity and Governance
"""
import json
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.tenants.models import AuditLog
from app.utils.logger import get_logger

logger = get_logger("audit")

class AuditService:
    """Service for managing audit logs and compliance"""

    def __init__(self, async_session_maker):
        self.async_session = async_session_maker

    async def log_action(
        self,
        organization_id: str,
        actor_id: str,
        actor_type: str,
        action: str,
        resource_type: str,
        resource_id: str,
        payload: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None
    ) -> bool:
        """Write an immutable audit log entry"""
        try:
            async with self.async_session() as session:
                log_entry = AuditLog(
                    organization_id=organization_id,
                    actor_id=actor_id,
                    actor_type=actor_type,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    payload=payload or {},
                    ip_address=ip_address
                )
                session.add(log_entry)
                await session.commit()
                return True
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
            return False

    async def get_audit_logs(
        self,
        organization_id: str,
        actor_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> list[Dict[str, Any]]:
        """Retrieve audit logs for compliance reporting"""
        try:
            async with self.async_session() as session:
                query = select(AuditLog).where(AuditLog.organization_id == organization_id)

                if actor_id:
                    query = query.where(AuditLog.actor_id == actor_id)
                if resource_type:
                    query = query.where(AuditLog.resource_type == resource_type)
                if action:
                    query = query.where(AuditLog.action == action)

                query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(limit)

                result = await session.execute(query)
                logs = result.scalars().all()

                return [
                    {
                        "id": str(log.id),
                        "organization_id": str(log.organization_id),
                        "actor_id": log.actor_id,
                        "actor_type": log.actor_type,
                        "action": log.action,
                        "resource_type": log.resource_type,
                        "resource_id": log.resource_id,
                        "payload": log.payload,
                        "ip_address": log.ip_address,
                        "created_at": log.created_at.isoformat() if log.created_at else None
                    }
                    for log in logs
                ]
        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}")
            return []

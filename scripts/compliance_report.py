#!/usr/bin/env python3
"""
compliance_report.py

Generates a SOC2 / ISO 27001 compliant audit report from the AuditLog table.
Usage: python3 scripts/compliance_report.py [organization_id]
"""

import asyncio
import csv
import os
import sys
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Ensure app imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.domain.tenants.models import AuditLog
from app.settings import get_settings


async def generate_report(org_id: str = None):
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    print("Generating SOC2 / ISO 27001 Audit Report...")
    if org_id:
        print(f"Filtering for Organization: {org_id}")
    
    report_filename = f"audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    
    async with async_session() as session:
        query = select(AuditLog)
        if org_id:
            query = query.where(AuditLog.organization_id == org_id)
        
        query = query.order_by(AuditLog.created_at.desc())
        
        try:
            result = await session.execute(query)
            logs = result.scalars().all()
        except Exception as e:
            print(f"Error querying database: {e}")
            return
    
    with open(report_filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        # SOC2 Standard Headers
        writer.writerow([
            "Timestamp", 
            "OrganizationID", 
            "ActorID", 
            "ActorType", 
            "Action", 
            "ResourceType", 
            "ResourceID", 
            "IPAddress", 
            "PayloadSummary"
        ])
        
        for log in logs:
            writer.writerow([
                log.created_at.isoformat() if log.created_at else "",
                str(log.organization_id),
                log.actor_id,
                log.actor_type,
                log.action,
                log.resource_type,
                log.resource_id,
                log.ip_address,
                str(log.payload) if log.payload else "{}"
            ])
            
    print(f"Report generated successfully: {report_filename}")
    print(f"Total events recorded: {len(logs)}")

if __name__ == "__main__":
    org_id = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(generate_report(org_id))

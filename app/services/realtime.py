import json
import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.container import get_container

logger = logging.getLogger("realtime_service")

class RealtimeService:
    """Service to publish operational events to Redis Pub/Sub for the dashboard."""

    def __init__(self, redis_client):
        self.redis = redis_client

    async def publish(
        self,
        org_id: str,
        topic: str,
        event_name: str,
        data: Dict[str, Any],
        severity: str = "info",
        source_id: Optional[str] = None,
        request_id: Optional[str] = None
    ):
        """
        Publish a normalized event to a tenant-scoped Redis channel.
        Allowed topics: "ingestion", "jobs", "errors", "metrics", "search"
        """
        if not self.redis:
            return

        channel = f"mercury:{org_id}:{topic}"
        payload = {
            "event": event_name,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "request_id": request_id,
            "source_id": source_id,
            "severity": severity,
            "data": data
        }

        try:
            await self.redis.redis.publish(channel, json.dumps(payload))
        except Exception as e:
            logger.error(f"Failed to publish to {channel}: {e}")

# Factory function for DI
def get_realtime_service(container=None):
    if not container:
        container = get_container()
    redis_client = container.get("redis")
    return RealtimeService(redis_client)

"""
Privacy Service - Layer 5: Domain
Manages tenant and user consent, data anonymization, and retention rules.
"""
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from app.domain.tenants.service import TenantService
from app.domain.users.service import UserService
from app.infrastructure.db.postgres import PostgresClient
from app.utils.logger import get_logger

logger = get_logger("privacy_service")


class PrivacyService:
    """Privacy and data retention business logic"""

    def __init__(self, db: PostgresClient, tenant_service: TenantService, user_service: UserService):
        self.db = db
        self.tenants = tenant_service
        self.users = user_service

    async def can_personalize(self, organization_id: str, user_id: str) -> bool:
        """
        Check if personalization is allowed for the given user.
        Rules:
        1. Tenant must have `enable_personalization == True`.
        2. User must have `has_consented_to_personalization == True`.
        """
        # 1. Check tenant config
        tenant_config = await self.tenants.get_tenant_config(organization_id)
        if not tenant_config or not tenant_config.enable_personalization:
            return False

        # 2. Check user consent
        profile = await self.users.get_user_profile(organization_id, user_id)
        if not profile:
            return False

        return bool(profile.get("has_consented_to_personalization", False))

    async def update_user_consent(self, organization_id: str, user_id: str, consent: bool) -> bool:
        """Update a user's consent for personalization."""
        success = await self.db.update_user(organization_id, user_id, {
            'has_consented_to_personalization': consent,
            'updated_at': datetime.now()
        })

        # If withdrawing consent, clear personalization data
        if success and not consent:
            await self._clear_personalization_data(organization_id, user_id)

        return success

    async def _clear_personalization_data(self, organization_id: str, user_id: str):
        """Clear a user's personalization signals (called on consent withdrawal)."""
        logger.info(f"Clearing personalization data for user {user_id} due to consent withdrawal.")
        # Clear preferences and behavior from postgres
        await self.db.update_user(organization_id, user_id, {
            'preferences': {},
            'behavior': {},
            'updated_at': datetime.now()
        })

        # Clear cache logic can be handled by UserService or cache events in the future.

    async def anonymize_user(self, organization_id: str, user_id: str) -> str:
        """
        Anonymize user records. Replaces PII with dummy data and retains only aggregate behavioral data.
        Returns the new anonymized user ID.
        """
        anon_id = f"anon_{uuid.uuid4().hex[:12]}"

        logger.info(f"Anonymizing user {user_id} -> {anon_id}")

        # In a real implementation we would update the user row with the new ID and scrub PII:
        # e.g., name="Anonymous", email=None, location=None, gender=None
        await self.db.update_user(organization_id, user_id, {
            'id': anon_id,
            'email': None,
            'name': "Anonymous",
            'gender': None,
            'location': {},
            'health': [],
            'extra_data': {},
            'has_consented_to_personalization': False,
            'updated_at': datetime.now()
        })

        return anon_id

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.addons.personalization.scorer import PersonalizationScorer
from app.domain.privacy.service import PrivacyService


@pytest.fixture
def mock_db():
    db = AsyncMock()
    return db

@pytest.fixture
def mock_tenant_service():
    tenant_service = AsyncMock()
    return tenant_service

@pytest.fixture
def mock_user_service():
    user_service = AsyncMock()
    return user_service

@pytest.mark.asyncio
async def test_privacy_service_can_personalize(mock_db, mock_tenant_service, mock_user_service):
    privacy_service = PrivacyService(mock_db, mock_tenant_service, mock_user_service)

    # 1. Tenant disabled, User enabled -> False
    mock_tenant_service.get_tenant_config.return_value = MagicMock(enable_personalization=False)
    mock_user_service.get_user_profile.return_value = {"has_consented_to_personalization": True}
    assert not await privacy_service.can_personalize("org_1", "user_1")

    # 2. Tenant enabled, User disabled -> False
    mock_tenant_service.get_tenant_config.return_value = MagicMock(enable_personalization=True)
    mock_user_service.get_user_profile.return_value = {"has_consented_to_personalization": False}
    assert not await privacy_service.can_personalize("org_1", "user_1")

    # 3. Tenant enabled, User missing -> False
    mock_user_service.get_user_profile.return_value = None
    assert not await privacy_service.can_personalize("org_1", "user_1")

    # 4. Tenant enabled, User enabled -> True
    mock_user_service.get_user_profile.return_value = {"has_consented_to_personalization": True}
    assert await privacy_service.can_personalize("org_1", "user_1")

@pytest.mark.asyncio
async def test_privacy_service_withdraw_consent(mock_db, mock_tenant_service, mock_user_service):
    privacy_service = PrivacyService(mock_db, mock_tenant_service, mock_user_service)

    mock_db.update_user.return_value = True

    # Withdrawing consent should clear data
    await privacy_service.update_user_consent("org_1", "user_1", False)

    # The first update is for consent, the second update should be to clear preferences/behavior
    assert mock_db.update_user.call_count == 2

    call_args = mock_db.update_user.call_args_list[1][0]
    update_dict = call_args[2]
    assert "preferences" in update_dict
    assert update_dict["preferences"] == {}
    assert "behavior" in update_dict
    assert update_dict["behavior"] == {}

@pytest.mark.asyncio
async def test_personalization_scorer_respects_privacy():
    mock_user_service = AsyncMock()
    mock_privacy_service = AsyncMock()
    mock_cache = AsyncMock()

    scorer = PersonalizationScorer(mock_user_service, mock_privacy_service, mock_cache)

    # Privacy disabled
    mock_privacy_service.can_personalize.return_value = False

    products = [{"id": "p1"}, {"id": "p2"}]
    scored = await scorer.score_products("org_1", "user_1", products)

    # Should return untouched products
    assert "personalization_score" not in scored[0]

    # Privacy enabled
    mock_privacy_service.can_personalize.return_value = True
    mock_user_service.get_user_profile.return_value = {}
    mock_cache.get_json.return_value = None

    scored_enabled = await scorer.score_products("org_1", "user_1", products)
    assert "personalization_score" in scored_enabled[0]

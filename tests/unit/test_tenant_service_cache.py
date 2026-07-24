from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.tenants.service import TenantService


@pytest.mark.asyncio
async def test_configuration_update_invalidates_tenant_context_and_search_cache():
    session = AsyncMock()
    session_context = MagicMock()
    session_context.__aenter__ = AsyncMock(return_value=session)
    session_context.__aexit__ = AsyncMock(return_value=False)

    db = MagicMock()
    db.async_session.return_value = session_context

    cache = AsyncMock()
    service = TenantService(db=db, cache=cache)

    assert await service.update_config(
        "00000000-0000-0000-0000-000000000001",
        enable_personalization=True,
    )

    cache.invalidate_tenant_contexts.assert_awaited_once_with(
        "00000000-0000-0000-0000-000000000001"
    )
    cache.bump_tenant_namespace_revision.assert_awaited_once_with(
        "00000000-0000-0000-0000-000000000001", "search"
    )

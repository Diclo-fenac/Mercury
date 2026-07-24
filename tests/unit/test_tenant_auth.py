from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.api import dependencies


@pytest.mark.asyncio
async def test_stress_test_key_is_not_an_authentication_bypass(monkeypatch):
    tenant_service = AsyncMock()
    tenant_service.validate_api_key.return_value = None
    container = MagicMock()
    container.get.return_value = tenant_service
    request = Request({"type": "http", "client": ("127.0.0.1", 12345), "headers": []})

    monkeypatch.setattr(dependencies, "check_rate_limit", AsyncMock(return_value=True))

    with pytest.raises(HTTPException) as exc_info:
        await dependencies.get_tenant_context(
            request=request,
            x_api_key="stress_test_key_123",
            container=container,
        )

    assert exc_info.value.status_code == 401
    tenant_service.validate_api_key.assert_awaited_once_with("stress_test_key_123")

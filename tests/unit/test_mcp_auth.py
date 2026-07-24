from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.api.dependencies import TenantContext
from app.mcp.auth import authenticate_mcp_request
from app.settings import get_settings


@pytest.fixture
def mock_container():
    container = MagicMock()
    tenant_service = AsyncMock()
    container.get.return_value = tenant_service
    return container

@pytest.mark.asyncio
async def test_authenticate_mcp_request_with_valid_api_key(mock_container):
    tenant_service = mock_container.get.return_value
    tenant_service.validate_api_key.return_value = {
        "organization_id": "org_123",
        "organization_slug": "test-org",
        "key_type": "public_search",
        "scopes": ["search"],
        "plan": "free",
        "config": {}
    }
    
    with patch("app.mcp.auth.get_container_dependency", return_value=mock_container):
        request = MagicMock()
        ctx = await authenticate_mcp_request(request, api_key="valid-key", bearer=None)
        assert ctx.organization_id == "org_123"
        assert ctx.collection_name == "tenant_org_123_products"

@pytest.mark.asyncio
async def test_authenticate_mcp_request_invalid_api_key(mock_container):
    tenant_service = mock_container.get.return_value
    tenant_service.validate_api_key.return_value = None
    
    with patch("app.mcp.auth.get_container_dependency", return_value=mock_container):
        request = MagicMock()
        with pytest.raises(HTTPException) as exc:
            await authenticate_mcp_request(request, api_key="invalid-key", bearer=None)
        assert exc.value.status_code == 401

@pytest.mark.asyncio
async def test_authenticate_mcp_request_valid_jwt(mock_container):
    tenant_service = mock_container.get.return_value
    
    from jose import jwt
    settings = get_settings()
    token = jwt.encode({"organization_id": "org_jwt", "roles": ["user"]}, settings.SECRET_KEY, algorithm="HS256")
    
    bearer = MagicMock()
    bearer.credentials = token
    
    with patch("app.mcp.auth.get_container_dependency", return_value=mock_container):
        request = MagicMock()
        ctx = await authenticate_mcp_request(request, api_key=None, bearer=bearer)
        assert ctx.organization_id == "org_jwt"
        assert ctx.key_type == "jwt_user"

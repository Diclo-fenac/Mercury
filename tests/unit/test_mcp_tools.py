import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.api.dependencies import TenantContext
from app.mcp.tools.catalog import get_categories, get_collections, get_product
from app.mcp.tools.search import autocomplete, search_documents, search_products


@pytest.fixture
def mock_context():
    return TenantContext(
        organization_id="org_test",
        organization_slug="org-test",
        key_type="public_search",
        scopes=["search"],
        plan="free",
        config={},
        collection_name="tenant_org_test_products"
    )

@pytest.fixture
def mock_container():
    container = MagicMock()

    search_service = AsyncMock()
    # Mock search_products result
    mock_result = MagicMock()
    mock_result.items = []
    search_service.search_products.return_value = mock_result

    typesense_mock = AsyncMock()

    container_mocks = {
        "search_orchestrator": search_service,
        "hybrid_search": AsyncMock(),
        "typesense": typesense_mock,
        "suggestions_service": AsyncMock(),
        "product_service": AsyncMock()
    }
    container.get.side_effect = lambda name: container_mocks.get(name)

    return container

@pytest.mark.asyncio
async def test_search_products_tool(mock_context, mock_container):
    with patch("app.mcp.tools.search.get_mcp_tenant_context", return_value=mock_context), \
         patch("app.mcp.tools.search.get_container", return_value=mock_container):

        result_json = await search_products(query="test", limit=5)
        result = json.loads(result_json)
        assert isinstance(result, list)

@pytest.mark.asyncio
async def test_search_documents_tool(mock_context, mock_container):
    with patch("app.mcp.tools.search.get_mcp_tenant_context", return_value=mock_context), \
         patch("app.mcp.tools.search.get_container", return_value=mock_container):

        mock_container.get("typesense").search.return_value = {"hits": [{"id": "doc1"}]}
        result_json = await search_documents(query="test", limit=5)
        result = json.loads(result_json)
        assert len(result) == 1
        assert result[0]["id"] == "doc1"

        # Verify collection isolation
        mock_container.get("typesense").search.assert_called_with(
            collection="tenant_org_test_documents",
            query="test",
            query_by="title,content",
            limit=5,
            page=1
        )

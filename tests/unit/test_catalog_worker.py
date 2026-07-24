from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.workers.catalog_worker import CatalogWorker


@pytest.mark.asyncio
async def test_reindex_catalog_success():
    # Setup mocks
    mock_typesense_client = MagicMock()
    mock_db = MagicMock()

    mock_client_inner = MagicMock()
    mock_typesense_client.client = mock_client_inner

    # Mock collections
    mock_collections_obj = MagicMock()
    mock_client_inner.collections = mock_collections_obj
    mock_collections_obj.create = AsyncMock()

    mock_collection_instance = MagicMock()
    mock_collections_obj.__getitem__.return_value = mock_collection_instance
    mock_collection_instance.documents.import_ = AsyncMock()
    mock_collection_instance.delete = AsyncMock()

    # Mock aliases
    mock_aliases_obj = MagicMock()
    mock_client_inner.aliases = mock_aliases_obj
    mock_aliases_obj.upsert = AsyncMock()

    mock_alias_instance = MagicMock()
    mock_aliases_obj.__getitem__.return_value = mock_alias_instance
    mock_alias_instance.retrieve = AsyncMock(return_value={"collection_name": "products_old"})

    worker = CatalogWorker(mock_typesense_client, mock_db)

    with patch("time.time", return_value=1234567890):
        res = await worker.reindex_catalog(
            "tenant_1",
            "tenant_1_products",
            {"name": "dummy"},
            [{"id": "1", "name": "Item"}]
        )

        assert res["success"] is True
        assert res["shadow_collection"] == "tenant_1_products_v1234567890"

        # Verify creation
        mock_collections_obj.create.assert_awaited_once_with({"name": "tenant_1_products_v1234567890"})

        # Verify import
        mock_collection_instance.documents.import_.assert_awaited_once_with(
            [{"id": "1", "name": "Item"}], {"action": "upsert"}
        )

        # Verify alias swap
        mock_aliases_obj.upsert.assert_awaited_once_with(
            "tenant_1_products", {"collection_name": "tenant_1_products_v1234567890"}
        )

        # Verify deletion of old
        mock_collection_instance.delete.assert_awaited_once()

@pytest.mark.asyncio
async def test_reindex_catalog_failure():
    # Setup mocks
    mock_typesense_client = MagicMock()
    mock_db = MagicMock()

    mock_client_inner = MagicMock()
    mock_typesense_client.client = mock_client_inner

    mock_collections_obj = MagicMock()
    mock_client_inner.collections = mock_collections_obj
    mock_collections_obj.create = AsyncMock(side_effect=Exception("Failed to create"))

    mock_collection_instance = MagicMock()
    mock_collections_obj.__getitem__.return_value = mock_collection_instance
    mock_collection_instance.delete = AsyncMock()

    worker = CatalogWorker(mock_typesense_client, mock_db)

    with pytest.raises(Exception, match="Failed to create"):
        await worker.reindex_catalog(
            "tenant_1",
            "tenant_1_products",
            {"name": "dummy"},
            []
        )

    mock_collection_instance.delete.assert_awaited_once()

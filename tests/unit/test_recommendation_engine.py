from unittest.mock import AsyncMock

import pytest

from app.domain.recommendations.engine import RecommendationEngine


@pytest.fixture
def mock_product_service():
    return AsyncMock()

@pytest.fixture
def mock_user_service():
    return AsyncMock()

@pytest.fixture
def mock_cache():
    return AsyncMock()

@pytest.mark.asyncio
async def test_get_frequently_bought_together_with_cache(mock_product_service, mock_user_service, mock_cache):
    engine = RecommendationEngine(mock_product_service, mock_user_service, mock_cache)
    
    # 1. Cache hit
    mock_cache.get_json.return_value = [{"id": "cached_prod"}]
    result = await engine.get_frequently_bought_together("org_1", "prod_1", 5)
    assert result == [{"id": "cached_prod"}]
    mock_product_service.get_product.assert_not_called()
    
    # 2. Cache miss
    mock_cache.get_json.return_value = None
    mock_product_service.get_product.return_value = {"id": "prod_1", "category": "Electronics"}
    mock_product_service.search_products.return_value = [{"id": "prod_2", "category": "Mobile Accessories"}]
    
    result = await engine.get_frequently_bought_together("org_1", "prod_1", 5)
    assert len(result) >= 1
    assert result[0]["id"] == "prod_2"
    assert mock_cache.set_json.called
    
@pytest.mark.asyncio
async def test_recommendation_caching_tenant_isolation(mock_product_service, mock_user_service, mock_cache):
    engine = RecommendationEngine(mock_product_service, mock_user_service, mock_cache)
    
    mock_cache.get_json.return_value = None
    mock_product_service.get_product.return_value = {"id": "prod_1", "category": "Clothing"}
    mock_product_service.search_products.return_value = []
    
    await engine.get_similar_products("org_1", "prod_1", 5)
    
    # Ensure cache key contains tenant hash prefix
    call_args = mock_cache.set_json.call_args[0]
    cache_key = call_args[0]
    assert "t-" in cache_key

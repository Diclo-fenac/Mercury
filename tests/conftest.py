"""
Test Configuration and Fixtures
"""
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

os.environ.setdefault("MERCURY_TEST_MODE", "true")

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client(mock_search_service, mock_product_service, mock_user_service, mock_image_service, mock_conversation_service):
    """Create test client with mock container dependency overrides"""
    # Import here to avoid circular imports
    from app.api.dependencies import (
        TenantContext,
        get_container_dependency,
        get_current_user,
        get_tenant_context,
        require_auth,
    )
    from main import app
    
    # Override authentication and tenant dependencies for testing
    test_identity = {
        "user_id": "test_user",
        "organization_id": "00000000-0000-0000-0000-000000000000",
        "authenticated": True,
        "roles": ["user", "admin"],
    }
    app.dependency_overrides[require_auth] = lambda: test_identity
    app.dependency_overrides[get_current_user] = lambda: test_identity
    
    dummy_tenant = TenantContext(
        organization_id="00000000-0000-0000-0000-000000000000",
        organization_slug="default-org",
        key_type="public_search",
        scopes=["search"],
        plan="free",
        config={
            "enable_semantic": True,
            "enable_personalization": False,
            "rrf_keyword_weight": 0.6,
            "rrf_vector_weight": 0.4,
            "out_of_stock_behavior": "demote"
        },
        collection_name="products"
    )
    app.dependency_overrides[get_tenant_context] = lambda: dummy_tenant
    
    # Configure mock container
    mock_container = MagicMock()
    
    # Mock recommendation orchestrator
    mock_rec_service = AsyncMock()
    mock_rec_service.get_personalized_recommendations = AsyncMock(return_value={
        "success": True,
        "recommendations": [],
        "personalization_type": "hybrid",
        "strategies_used": []
    })
    mock_rec_service.get_product_recommendations = AsyncMock(return_value={
        "success": True,
        "recommendations": []
    })
    
    # Mock chat orchestrator
    mock_chat_service = AsyncMock()
    
    mock_container.get.side_effect = lambda service_name: {
        'search_orchestrator': mock_search_service,
        'product_orchestrator': mock_product_service,
        'user_orchestrator': mock_user_service,
        'recommendation_orchestrator': mock_rec_service,
        'image_orchestrator': mock_image_service,
        'conversation_orchestrator': mock_conversation_service,
        'chat_orchestrator': mock_chat_service
    }.get(service_name)
    
    app.dependency_overrides[get_container_dependency] = lambda: mock_container
    
    yield TestClient(app)
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_cache():
    """Create mock cache client"""
    cache = AsyncMock()
    cache.get_json = AsyncMock(return_value=None)
    cache.set_json = AsyncMock(return_value=True)
    cache.delete = AsyncMock(return_value=True)
    cache.clear = AsyncMock(return_value=True)
    return cache


@pytest.fixture
def mock_postgres():
    """Create mock Postgres client"""
    postgres = AsyncMock()
    postgres.collection = MagicMock()
    return postgres


@pytest.fixture
def mock_search_service():
    """Create mock search service"""
    service = AsyncMock()
    service.search_products = AsyncMock(return_value={
        "success": True,
        "products": [],
        "total": 0
    })
    service.get_suggestions = AsyncMock(return_value={
        "success": True,
        "suggestions": []
    })
    service.get_trending_searches = AsyncMock(return_value={
        "success": True,
        "searches": []
    })
    service.get_popular_searches = AsyncMock(return_value={
        "success": True,
        "searches": []
    })
    service.handle = AsyncMock(return_value={
        "success": True,
        "results": [],
        "total_results": 0
    })
    return service


@pytest.fixture
def mock_product_service():
    """Create mock product service"""
    service = AsyncMock()
    service.get_product_by_id = AsyncMock(return_value={
        "success": True,
        "product": {
            "id": "test_id",
            "title": "Test Product",
            "price": {"selling": 100}
        }
    })
    service.get_product_details = AsyncMock(return_value={
        "success": True,
        "product": {
            "id": "test_id",
            "title": "Test Product",
            "price": {"selling": 100}
        }
    })
    service.get_trending_products = AsyncMock(return_value={
        "success": True,
        "products": [],
        "criteria": "views_and_purchases"
    })
    service.get_deals = AsyncMock(return_value={
        "success": True,
        "deals": [],
        "average_discount": 0
    })
    service.get_flash_deals = AsyncMock(return_value={
        "success": True,
        "deals": []
    })
    service.get_brand_deals = AsyncMock(return_value={
        "success": True,
        "deals": []
    })
    return service


@pytest.fixture
def mock_user_service():
    """Create mock user service"""
    service = AsyncMock()
    service.get_user_profile = AsyncMock(return_value={
        "success": True,
        "profile": {
            "user_id": "test_user",
            "preferences": {},
            "activity_summary": {}
        }
    })
    service.get_user_preferences = AsyncMock(return_value={
        "success": True,
        "preferences": {}
    })
    service.get_user_activity = AsyncMock(return_value={
        "success": True,
        "activities": []
    })
    service.get_personalized_recommendations = AsyncMock(return_value={
        "success": True,
        "recommendations": [],
        "personalization_type": "hybrid"
    })
    service.get_similar_users_recommendations = AsyncMock(return_value={
        "success": True,
        "recommendations": [],
        "similar_users_count": 0
    })
    service.get_frequently_bought_together = AsyncMock(return_value={
        "success": True,
        "products": []
    })
    return service


@pytest.fixture
def mock_image_service():
    """Create mock image service"""
    service = AsyncMock()
    service.process_image_upload = AsyncMock(return_value={
        "success": True,
        "image_id": "test_image_id",
        "image_url": "http://example.com/image.jpg"
    })
    service.analyze_image = AsyncMock(return_value={
        "success": True,
        "analysis": {
            "description": "Test image",
            "is_barcode": False
        }
    })
    service.get_cached_analysis = AsyncMock(return_value={
        "success": True,
        "analysis": {}
    })
    service.search_by_image = AsyncMock(return_value={
        "success": True,
        "results": [],
        "image_analysis": {}
    })
    service.get_image_metadata = AsyncMock(return_value={
        "success": True,
        "image": {
            "id": "test_image_id",
            "url": "http://example.com/image.jpg",
            "analysis": {"description": "Test image"}
        }
    })
    return service


@pytest.fixture
def mock_conversation_service():
    """Create mock conversation service"""
    service = AsyncMock()
    service.get_conversations = AsyncMock(return_value={
        "success": True,
        "conversations": []
    })
    service.get_user_conversations = AsyncMock(return_value={
        "success": True,
        "conversations": [],
        "total": 0
    })
    service.get_conversation = AsyncMock(return_value={
        "success": True,
        "conversation": {
            "id": "test_conv",
            "messages": []
        }
    })
    service.get_conversation_details = AsyncMock(return_value={
        "success": True,
        "conversation": {
            "id": "test_conv",
            "messages": []
        }
    })
    service.create_conversation = AsyncMock(return_value={
        "success": True,
        "conversation_id": "new_conv_id"
    })
    service.delete_conversation = AsyncMock(return_value={
        "success": True
    })
    return service


@pytest.fixture
def sample_product():
    """Sample product data"""
    return {
        "id": "prod_123",
        "title": "Wireless Headphones",
        "description": "High-quality wireless headphones",
        "brand": "Sony",
        "category": "Electronics",
        "price": {
            "original": 200,
            "selling": 150
        },
        "rating": 4.5,
        "stock": "In Stock",
        "images": ["http://example.com/image1.jpg"],
        "tags": {"color": "black", "type": "over-ear"}
    }


@pytest.fixture
def sample_user():
    """Sample user data"""
    return {
        "user_id": "user_123",
        "preferences": {
            "favorite_categories": ["Electronics", "Fashion"],
            "price_range": {"min": 0, "max": 1000}
        },
        "activity_summary": {
            "total_views": 50,
            "total_purchases": 5
        }
    }


@pytest.fixture
def sample_search_query():
    """Sample search query"""
    return {
        "query": "wireless headphones",
        "user_id": "user_123",
        "filters": {"category": "Electronics"},
        "limit": 10
    }


@pytest.fixture
def sample_image_data():
    """Sample base64 image data"""
    return "data:image/jpeg;base64,/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8VAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="



@pytest.fixture
def sample_conversation():
    """Sample conversation data"""
    return {
        "conversation_id": "conv_123",
        "title": "Shopping Help",
        "messages": [
            {
                "message_id": "msg_1",
                "user_id": "user_123",
                "message": "Show me laptops",
                "timestamp": "2024-01-23T10:00:00Z"
            }
        ]
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "asyncio: mark test as async"
    )


def pytest_collection_modifyitems(config, items):
    """External-service suites run only when an operator explicitly enables them."""
    if os.getenv("MERCURY_RUN_INTEGRATION") == "1":
        return
    skip = pytest.mark.skip(reason="Set MERCURY_RUN_INTEGRATION=1 with Docker services to run integration tests.")
    for item in items:
        if "/tests/integration/" in str(item.fspath):
            item.add_marker(skip)


# Async test support provided by pytest-asyncio natively

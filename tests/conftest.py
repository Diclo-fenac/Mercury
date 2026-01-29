"""
Test Configuration and Fixtures
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


@pytest.fixture
def client():
    """Create test client"""
    # Import here to avoid circular imports
    from main import app
    return TestClient(app)


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
def mock_firestore():
    """Create mock Firestore client"""
    firestore = AsyncMock()
    firestore.collection = MagicMock()
    return firestore


@pytest.fixture
def mock_search_service():
    """Create mock search service"""
    service = AsyncMock()
    service.search_products = AsyncMock(return_value={
        "success": True,
        "products": [],
        "total": 0
    })
    service.get_suggestions = AsyncMock(return_value=[])
    service.get_trending_searches = AsyncMock(return_value=[])
    service.get_popular_searches = AsyncMock(return_value=[])
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
        "data": {
            "preferences": {},
            "activity_summary": {}
        }
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
    return service


@pytest.fixture
def mock_conversation_service():
    """Create mock conversation service"""
    service = AsyncMock()
    service.get_conversations = AsyncMock(return_value={
        "success": True,
        "conversations": []
    })
    service.get_conversation = AsyncMock(return_value={
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
}


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


# Async test support
@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

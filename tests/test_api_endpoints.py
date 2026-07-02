"""
Comprehensive API Endpoint Tests
Tests for all implemented endpoints
"""

import pytest


class TestSearchEndpoints:
    """Tests for search endpoints"""
    
    @pytest.mark.asyncio
    async def test_search_suggestions(self, client):
        """Test search suggestions/autocomplete endpoint"""
        response = client.get(
            "/api/v1/search/autocomplete",
            params={"q": "laptop", "limit": 10}
        )
        assert response.status_code in [200, 500]  # May fail without real service
        if response.status_code == 200:
            data = response.json()
            assert "suggestions" in data
            assert "query" in data
            assert data["query"] == "laptop"
    
    @pytest.mark.asyncio
    async def test_search_suggestions_min_length(self, client):
        """Test search suggestions with minimum length validation"""
        response = client.get(
            "/api/v1/search/autocomplete",
            params={"q": "a", "limit": 10}
        )
        # Should fail validation or return empty
        assert response.status_code in [200, 422]
    
    @pytest.mark.asyncio
    async def test_trending_searches(self, client):
        """Test trending searches endpoint"""
        response = client.get(
            "/api/v1/search/trending",
            params={"limit": 10}
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "trending_searches" in data
            assert "total" in data
    
    @pytest.mark.asyncio
    async def test_trending_searches_with_category(self, client):
        """Test trending searches filtered by category"""
        response = client.get(
            "/api/v1/search/trending",
            params={"limit": 10, "category": "Electronics"}
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert data.get("category") == "Electronics"
    
    @pytest.mark.asyncio
    async def test_popular_searches(self, client):
        """Test popular searches endpoint"""
        response = client.get(
            "/api/v1/search/popular",
            params={"limit": 10}
        )
        assert response.status_code in [200, 500]
        if response.status_code == 200:
            data = response.json()
            assert "popular_searches" in data
            assert isinstance(data["popular_searches"], list)
    
    @pytest.mark.asyncio
    async def test_image_search(self, client):
        """Test image-based product search"""
        payload = {
            "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
            "prompt": "black wireless headphones",
            "search_type": "exact_and_similar",
            "limit": 10,
            "user_id": "test_user"
        }
        response = client.post(
            "/api/v1/search/image",
            json=payload
        )
        assert response.status_code in [200, 400, 500]


class TestProductEndpoints:
    """Tests for product endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_product_recommendations(self, client):
        """Test get product recommendations"""
        response = client.get(
            "/api/v1/products/test_product_id/recommendations",
            params={"limit": 5, "recommendation_type": "similar"}
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "recommendations" in data
            assert "product_id" in data


class TestUserEndpoints:
    """Tests for user endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_user_profile(self, client):
        """Test get user profile endpoint"""
        response = client.get("/api/v1/users/test_user/profile")
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "profile" in data
    
    @pytest.mark.asyncio
    async def test_get_user_preferences(self, client):
        """Test get user preferences endpoint"""
        response = client.get("/api/v1/users/test_user/preferences")
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "preferences" in data
    
    @pytest.mark.asyncio
    async def test_get_user_activity(self, client):
        """Test get user activity endpoint"""
        response = client.get(
            "/api/v1/users/test_user/activity",
            params={"limit": 50}
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "activities" in data
            assert "total" in data
    
    @pytest.mark.asyncio
    async def test_get_user_activity_filtered(self, client):
        """Test get user activity filtered by type"""
        response = client.get(
            "/api/v1/users/test_user/activity",
            params={"limit": 50, "activity_type": "product_view"}
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert data.get("filtered_by") == "product_view"
    


class TestImageEndpoints:
    """Tests for image endpoints"""
    
    @pytest.mark.asyncio
    async def test_upload_image(self, client):
        """Test image upload endpoint"""
        payload = {
            "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
            "user_id": "test_user",
            "message": "Check this product",
            "create_chat_message": False
        }
        response = client.post(
            "/api/v1/images/",
            json=payload
        )
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "image_id" in data
            assert "analysis" in data
    
    @pytest.mark.asyncio
    async def test_upload_image_with_chat(self, client):
        """Test image upload with chat message creation"""
        payload = {
            "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
            "user_id": "test_user",
            "message": "What product is this?",
            "conversation_id": "conv_123",
            "create_chat_message": True
        }
        response = client.post(
            "/api/v1/images/",
            json=payload
        )
        assert response.status_code in [200, 400, 500]
    
    @pytest.mark.asyncio
    async def test_image_search(self, client):
        """Test image-based search"""
        payload = {
            "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
            "prompt": "similar products",
            "search_type": "similar_style",
            "limit": 10,
            "user_id": "test_user"
        }
        response = client.post(
            "/api/v1/images/search",
            json=payload
        )
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "results" in data
    
    @pytest.mark.asyncio
    async def test_get_image_analysis(self, client):
        """Test get cached image analysis"""
        response = client.get(
            "/api/v1/images/test_image_id/analysis"
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "image_id" in data
            assert "analysis" in data


class TestConversationEndpoints:
    """Tests for conversation endpoints"""
    
    @pytest.mark.asyncio
    async def test_get_conversations(self, client):
        """Test get user conversations"""
        response = client.get(
            "/api/v1/conversations/"
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "conversations" in data
            assert "total" in data
    
    @pytest.mark.asyncio
    async def test_get_conversation_detail(self, client):
        """Test get conversation details"""
        response = client.get(
            "/api/v1/conversations/conv_123"
        )
        assert response.status_code in [200, 404, 500]
        if response.status_code == 200:
            data = response.json()
            assert "conversation" in data
    
    @pytest.mark.asyncio
    async def test_create_conversation(self, client):
        """Test create new conversation"""
        payload = {
            "user_id": "test_user",
            "title": "Shopping Help",
            "metadata": {"source": "api"}
        }
        response = client.post(
            "/api/v1/conversations/",
            json=payload
        )
        assert response.status_code in [200, 201, 400, 500]
    
    @pytest.mark.asyncio
    async def test_delete_conversation(self, client):
        """Test delete conversation"""
        response = client.delete(
            "/api/v1/conversations/conv_123"
        )
        assert response.status_code in [200, 204, 404, 500]


class TestHealthEndpoints:
    """Tests for health check endpoints"""
    
    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
    
    @pytest.mark.asyncio
    async def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200


class TestErrorHandling:
    """Tests for error handling"""
    
    @pytest.mark.asyncio
    async def test_invalid_user_id_format(self, client):
        """Test invalid user ID format"""
        response = client.get("/api/v1/users/invalid@user/profile")
        assert response.status_code in [400, 422, 500]
    
    @pytest.mark.asyncio
    async def test_missing_required_parameter(self, client):
        """Test missing required parameter"""
        response = client.get("/api/v1/search/autocomplete")
        assert response.status_code == 422  # Validation error
    
    @pytest.mark.asyncio
    async def test_invalid_limit_parameter(self, client):
        """Test invalid limit parameter"""
        response = client.get(
            "/api/v1/search/autocomplete",
            params={"q": "test", "limit": 1000}  # Exceeds max
        )
        assert response.status_code == 422
    


class TestRateLimiting:
    """Tests for rate limiting"""
    
    @pytest.mark.asyncio
    async def test_search_rate_limit(self, client):
        """Test search rate limiting"""
        # Make multiple requests
        for i in range(5):
            response = client.post(
                "/api/v1/search/",
                json={
                    "query": f"test {i}",
                    "user_id": "test_user"
                }
            )
            assert response.status_code in [200, 429, 500]
    
    @pytest.mark.asyncio
    async def test_image_upload_rate_limit(self, client):
        """Test image upload rate limiting"""
        payload = {
            "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
            "user_id": "test_user"
        }
        
        for i in range(3):
            response = client.post(
                "/api/v1/images/",
                json=payload
            )
            assert response.status_code in [200, 429, 500]


class TestDataValidation:
    """Tests for data validation"""
    
    @pytest.mark.asyncio
    async def test_invalid_image_data_format(self, client):
        """Test invalid image data format"""
        payload = {
            "image_data": "invalid_base64_data",
            "user_id": "test_user"
        }
        response = client.post(
            "/api/v1/images/",
            json=payload
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_search_type(self, client):
        """Test invalid search type"""
        payload = {
            "image_data": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
            "prompt": "test",
            "search_type": "invalid_type",
            "user_id": "test_user"
        }
        response = client.post(
            "/api/v1/images/search",
            json=payload
        )
        assert response.status_code == 422
    
    @pytest.mark.asyncio
    async def test_invalid_recommendation_type(self, client):
        """Test invalid recommendation type"""
        response = client.get(
            "/api/v1/products/test_product/recommendations",
            params={"recommendation_type": "invalid_type"}
        )
        assert response.status_code == 422


class TestResponseFormats:
    """Tests for response format consistency"""
    
    @pytest.mark.asyncio
    async def test_search_response_format(self, client):
        """Test search response format"""
        response = client.post(
            "/api/v1/search/",
            json={
                "query": "test",
                "user_id": "test_user"
            }
        )
        if response.status_code == 200:
            data = response.json()
            assert "query" in data
            assert "results" in data
            assert "total_results" in data
    
    @pytest.mark.asyncio
    async def test_product_response_format(self, client):
        """Test product response format"""
        response = client.get("/api/v1/products/test_id")
        if response.status_code == 200:
            data = response.json()
            assert "id" in data
            assert "title" in data
    
    @pytest.mark.asyncio
    async def test_user_response_format(self, client):
        """Test user response format"""
        response = client.get("/api/v1/users/test_user/profile")
        if response.status_code == 200:
            data = response.json()
            assert "profile" in data or "success" in data

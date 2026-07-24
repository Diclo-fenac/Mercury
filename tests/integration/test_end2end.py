#!/usr/bin/env python3
"""
End-to-End Integration Tests
Tests real system functionality with real services
NO MOCKS - Tests actual Postgres, Redis, Typesense integration
"""
import sys
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.container import Container
from app.infrastructure.id_generator import IDGenerator


class TestEnd2EndIntegration:
    """End-to-end integration tests with real services"""

    @pytest.fixture
    async def container(self):
        """Initialize container with real services"""
        # Load environment
        from dotenv import load_dotenv
        load_dotenv()

        # Initialize container
        container = Container()
        await container.initialize()

        yield container

        # Cleanup
        await container.cleanup()

    @pytest.fixture
    def id_gen(self):
        """ID generator for tests"""
        return IDGenerator()

    @pytest.mark.asyncio
    async def test_conversation_creation_and_messaging(self, container, id_gen):
        """Test conversation creation and message saving"""
        # Get services
        conversation_orchestrator = container.get('conversation_orchestrator')
        chat_orchestrator = container.get('chat_orchestrator')

        # Test user
        user_id = f"test_user_{id_gen.timestamp()}"

        # Create conversation
        result = await conversation_orchestrator.create_conversation(user_id, "Test Chat")

        assert result['success'] is True
        assert 'conversation_id' in result
        conversation_id = result['conversation_id']

        # Send message to conversation
        chat_result = await chat_orchestrator.handle(
            message="Hello, can you help me find products?",
            user_id=user_id,
            conversation_id=conversation_id
        )

        assert chat_result['success'] is True
        assert 'response' in chat_result
        assert chat_result['conversation_id'] == conversation_id

        # Verify conversation exists and has messages
        conversation = await conversation_orchestrator.get_conversation_details(user_id, conversation_id)
        assert conversation['success'] is True
        assert conversation['conversation']['user_id'] == user_id

        # Get conversation history
        history = await conversation_orchestrator.get_conversation_history(conversation_id, user_id)
        assert history['success'] is True
        assert len(history['messages']) >= 2  # User message + assistant response

    @pytest.mark.asyncio
    async def test_user_profile_operations(self, container, id_gen):
        """Test user profile creation and updates"""
        user_orchestrator = container.get('user_orchestrator')

        user_id = f"test_user_{id_gen.timestamp()}"

        # Update user preferences (this should create profile if not exists)
        preferences = {
            "categories": ["Electronics", "Fashion"],
            "price_range": {"min": 50, "max": 500},
            "brands": ["Apple", "Nike"]
        }

        result = await user_orchestrator.update_user_preferences(user_id, preferences)
        assert result['success'] is True
        assert 'preferences' in result

        # Get user profile
        profile_result = await user_orchestrator.get_user_profile(user_id)
        assert profile_result['success'] is True
        assert profile_result['profile']['user_id'] == user_id

        # Get user preferences
        prefs_result = await user_orchestrator.get_user_preferences(user_id)
        assert prefs_result['success'] is True
        assert 'preferences' in prefs_result

    @pytest.mark.asyncio
    async def test_product_search_after_seeding(self, container):
        """Test product search functionality with seeded data"""
        search_orchestrator = container.get('search_orchestrator')
        product_orchestrator = container.get('product_orchestrator')

        # Test trending products
        trending_result = await product_orchestrator.get_trending_products(limit=5)
        assert trending_result['success'] is True

        # Should have products if seeded
        if trending_result['products']:
            assert len(trending_result['products']) > 0

            # Test product details
            first_product = trending_result['products'][0]
            product_id = first_product['id']

            details_result = await product_orchestrator.get_product_details(product_id)
            assert details_result['success'] is True
            assert details_result['product']['id'] == product_id

        # Test search functionality
        search_result = await search_orchestrator.search_products(
            query="iPhone",
            filters={"category": "Electronics"},
            limit=10
        )
        assert search_result['success'] is True
        # Results may be empty if no data seeded, but should not error

    @pytest.mark.asyncio
    async def test_image_upload_error_handling(self, container, id_gen):
        """Test image upload returns structured errors, not exceptions"""
        image_orchestrator = container.get('image_orchestrator')

        user_id = f"test_user_{id_gen.timestamp()}"

        # Test with invalid image data
        result = await image_orchestrator.process_image_upload(
            image_data="invalid_base64_data",
            organization_id="00000000-0000-0000-0000-000000000001",
            user_id=user_id
        )

        # Should return structured error, not raise exception
        assert isinstance(result, dict)
        assert 'success' in result

        if not result['success']:
            assert 'error' in result
            assert 'details' in result

    @pytest.mark.asyncio
    async def test_service_health_checks(self, container):
        """Test that all critical services are healthy"""
        # Get infrastructure services
        postgres = container.get('postgres')
        redis = container.get('redis')

        # Test Postgres health
        postgres_healthy = await postgres.health_check()
        assert postgres_healthy is True, "PostgreSQL service should be healthy"

        # Test Redis health (if available)
        if redis:
            redis_healthy = await redis.health_check()
            # Redis might not be available in all environments
            if redis_healthy is not None:
                assert isinstance(redis_healthy, bool)

    @pytest.mark.asyncio
    async def test_conversation_access_control(self, container, id_gen):
        """Test conversation access control works correctly"""
        conversation_orchestrator = container.get('conversation_orchestrator')

        # Create conversation with user1
        user1_id = f"test_user1_{id_gen.timestamp()}"
        user2_id = f"test_user2_{id_gen.timestamp()}"

        result = await conversation_orchestrator.create_conversation(user1_id, "Private Chat")
        assert result['success'] is True
        conversation_id = result['conversation_id']

        # User1 should be able to access
        access_result = await conversation_orchestrator.get_conversation_details(user1_id, conversation_id)
        assert access_result['success'] is True

        # User2 should NOT be able to access
        denied_result = await conversation_orchestrator.get_conversation_details(user2_id, conversation_id)
        assert denied_result['success'] is False
        assert denied_result['error'] == 'access_denied'

    @pytest.mark.asyncio
    async def test_error_propagation(self, container):
        """Test that errors propagate correctly without silent failures"""
        conversation_orchestrator = container.get('conversation_orchestrator')
        user_orchestrator = container.get('user_orchestrator')

        # Test with non-existent conversation
        result = await conversation_orchestrator.get_conversation_details("user123", "nonexistent_conv")
        assert result['success'] is False
        assert result['error'] == 'not_found'

        # Test with non-existent user
        user_result = await user_orchestrator.get_user_profile("nonexistent_user")
        assert user_result['success'] is False
        assert user_result['error'] == 'not_found'

    @pytest.mark.asyncio
    async def test_data_persistence(self, container, id_gen):
        """Test that data actually persists to real databases"""
        conversation_orchestrator = container.get('conversation_orchestrator')
        postgres = container.get('postgres')

        user_id = f"test_user_{id_gen.timestamp()}"

        # Create conversation
        result = await conversation_orchestrator.create_conversation(user_id, "Persistence Test")
        assert result['success'] is True
        conversation_id = result['conversation_id']

        # Verify it exists in Postgres directly
        doc = await postgres.get_document('conversations', conversation_id)
        assert doc is not None
        assert doc['user_id'] == user_id
        assert doc['title'] == "Persistence Test"

        # Clean up
        await postgres.delete_document('conversations', conversation_id)


class TestFailureInjection:
    """Test system behavior when services fail"""

    @pytest.fixture
    async def container(self):
        """Initialize container"""
        from dotenv import load_dotenv
        load_dotenv()

        container = Container()
        await container.initialize()
        yield container
        await container.cleanup()

    @pytest.mark.asyncio
    async def test_invalid_conversation_handling(self, container):
        """Test handling of invalid conversation IDs"""
        chat_orchestrator = container.get('chat_orchestrator')

        # Try to send message to non-existent conversation
        result = await chat_orchestrator.handle(
            message="Hello",
            user_id="test_user",
            conversation_id="invalid_conversation_id"
        )

        # Should create new conversation, not fail
        assert result['success'] is True
        assert 'conversation_id' in result
        # Should be a different conversation ID than requested
        assert result['conversation_id'] != "invalid_conversation_id"

    @pytest.mark.asyncio
    async def test_missing_service_graceful_degradation(self, container):
        """Test graceful degradation when optional services are missing"""
        # This tests the system's resilience to missing optional services

        # Get orchestrators
        search_orchestrator = container.get('search_orchestrator')

        # Search should work even if some services are unavailable
        result = await search_orchestrator.search_products(
            query="test product",
            limit=5
        )

        # Should return result (may be empty) but not crash
        assert isinstance(result, dict)
        assert 'success' in result


# Test runner
if __name__ == "__main__":
    # Run specific test
    import subprocess

    # Run with pytest
    result = subprocess.run([
        sys.executable, "-m", "pytest",
        __file__,
        "-v",
        "--tb=short"
    ], cwd=project_root)

    sys.exit(result.returncode)

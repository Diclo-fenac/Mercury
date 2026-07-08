import pytest
from fastapi.testclient import TestClient
import time
import asyncio
from unittest.mock import patch, MagicMock
from app.infrastructure.cache.redis import RedisClient
from app.core.config import Settings
import json

import os

@pytest.fixture(scope="session", autouse=True)
def setup_env():
    """Ensure environment is loaded"""
    from dotenv import load_dotenv
    load_dotenv()

    # Point to localhost if running outside docker
    db_url = os.environ.get("DATABASE_URL", "")
    if "postgres:" in db_url and "@postgres:" in db_url:
        os.environ["DATABASE_URL"] = db_url.replace("@postgres:", "@localhost:")

    redis_url = os.environ.get("REDIS_URL", "")
    if "redis:" in redis_url and "//redis:" in redis_url:
        os.environ["REDIS_URL"] = redis_url.replace("//redis:", "//localhost:")

    os.environ["REDIS_HOST"] = "localhost"
    os.environ["TYPESENSE_HOST"] = "localhost"

    # Clear settings cache so it picks up the patched os.environ
    from app.settings import get_settings
    get_settings.cache_clear()

    # Clear container instance
    import app.container
    app.container.container_instance = None

@pytest.fixture(scope="module")
def client(setup_env):
    # Setup test configuration
    from main import app
    app.dependency_overrides = {}
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture(autouse=True)
def mock_auth():
    """Mock the require_admin_key dependency"""
    from main import app
    from app.api.dependencies import require_admin_key, get_tenant_context
    from fastapi import Request
    
    def override_require_admin_key(request: Request = None):
        from app.api.dependencies import TenantContext
        return TenantContext(
            organization_id="00000000-0000-0000-0000-000000000000",
            organization_slug="org-test",
            key_type="public_search",
            scopes=["search"],
            plan="enterprise",
            config={"enable_personalization": True, "out_of_stock_behavior": "hide"},
            collection_name="tenant_org_test_products"
        )
    
    app.dependency_overrides[require_admin_key] = override_require_admin_key
    app.dependency_overrides[get_tenant_context] = override_require_admin_key
    yield
    app.dependency_overrides.clear()

class TestSREMetrics:
    
    def test_log_click_event(self, client):
        """1. Log a click event -> HTTP 202"""
        payload = {
            "event_type": "click",
            "product_id": "p001",
            "query": "gaming mouse",
            "user_id": "u001"
        }
        
        response = client.post(
            "/api/v1/telemetry/events",
            json=payload,
            headers={"x-tenant-id": "org_test"}
        )
        
        # Test requires a 202
        assert response.status_code == 202, f"Expected 202, got {response.status_code}: {response.text}"
        data = response.json()
        assert data["success"] is True

    def test_verify_trending_update(self, client):
        """2. & 3. Verify trending update for query in Redis and API"""
        # Fire 10 telemetry events
        for _ in range(10):
            response = client.post(
                "/api/v1/telemetry/events",
                json={
                    "event_type": "search",
                    "query": "gaming mouse test",
                    "user_id": "u002"
                },
                headers={"x-tenant-id": "org_test"}
            )
            assert response.status_code == 202
            
        # Give background tasks a moment to complete
        time.sleep(0.1)
        
        # Verify via trending endpoint
        trending_resp = client.get(
            "/api/v1/search/trending",
            headers={"x-tenant-id": "org_test"}
        )
        
        assert trending_resp.status_code == 200
        data = trending_resp.json()
        assert "trending_searches" in data
        assert isinstance(data["trending_searches"], list)
        
        # gaming mouse test should be in the list
        found = any("gaming mouse test" in search for search in data["trending_searches"])
        assert found, f"Query 'gaming mouse test' not found in trending searches: {data['trending_searches']}"

    def test_fetch_system_metrics(self, client):
        """4. Fetch system metrics"""
        resp = client.get("/api/v1/admin/system/metrics")
        assert resp.status_code == 200
        data = resp.json()
        assert "cpu_percent" in data
        assert "ram_percent" in data
        assert "gpu_enabled" in data
        assert "gpu_name" in data

    def test_prometheus_metrics(self, client):
        """6. Prometheus metrics endpoint"""
        resp = client.get("/metrics")
        assert resp.status_code == 200
        assert "text/plain" in resp.headers["content-type"]
        assert "http_requests" in resp.text.lower() or "python_" in resp.text.lower()

    def test_health_check(self, client):
        """7. Health check"""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "healthy"

    def test_simulated_failure_redis(self, client):
        """9. Simulated failure (graceful degradation)"""
        # We can simulate failure by temporarily patching the container's cache
        from app.container import Container
        from main import app

        container_instance = app.state.container
        search_orchestrator = container_instance.get("search_orchestrator")
        original_cache = search_orchestrator.cache

        # Set cache to None to simulate Redis down
        search_orchestrator.cache = None

        try:
            # Should still return 200 and search results (degraded)
            resp = client.post("/api/v1/search/", json={"query": "laptop"}, headers={"x-tenant-id": "org_test"})
            if resp.status_code != 200:
                print(resp.json())
            assert resp.status_code == 200
        finally:
            # Restore Redis
            search_orchestrator.cache = original_cache

    def test_simulated_failure_typesense(self, client):
        """10. Simulated failure Typesense"""
        from main import app
        container_instance = app.state.container
        search_orchestrator = container_instance.get("search_orchestrator")
        original_typesense = search_orchestrator.search.typesense
        
        # Set db to None to simulate Typesense down
        search_orchestrator.search.typesense = None
        
        try:
            # Query should degrade gracefully to Postgres and return 200 OK
            resp = client.post("/api/v1/search/", json={"query": "laptop"}, headers={"x-tenant-id": "org_test"})
            if resp.status_code != 200:
                print(resp.json())
            assert resp.status_code == 200
        finally:
            # Restore db
            search_orchestrator.search.typesense = original_typesense

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def admin_client():
    from app.api.dependencies import TenantContext, get_container_dependency, require_admin_key
    from app.main import app
    
    # Mock admin tenant
    dummy_admin_tenant = TenantContext(
        organization_id="00000000-0000-0000-0000-000000000000",
        organization_slug="default-org",
        key_type="private_admin",
        scopes=["admin"],
        plan="free",
        config={},
        collection_name="products"
    )
    
    # Mock tenant service methods
    mock_tenant_service = AsyncMock()
    mock_tenant_service.get_config.return_value = {"webhook_urls": ["https://example.com/hook"]}
    mock_tenant_service.update_config.return_value = True
    mock_tenant_service.get_all_synonyms.return_value = [{"term": "sneaker", "synonyms": ["shoe", "kick"]}]
    mock_tenant_service.add_synonym.return_value = True
    mock_tenant_service.remove_synonym.return_value = True

    # Mock container
    mock_container = MagicMock()
    mock_container.get.side_effect = lambda key: mock_tenant_service if key == "tenant_service" else None

    # Overrides
    app.dependency_overrides[require_admin_key] = lambda: dummy_admin_tenant
    app.dependency_overrides[get_container_dependency] = lambda: mock_container
    
    with TestClient(app) as client:
        yield client
        
    app.dependency_overrides.clear()

def test_get_webhooks(admin_client):
    response = admin_client.get("/api/v1/admin/webhooks")
    assert response.status_code == 200
    assert "webhook_urls" in response.json()
    assert response.json()["webhook_urls"] == ["https://example.com/hook"]

def test_update_webhooks(admin_client):
    response = admin_client.post("/api/v1/admin/webhooks", json={"webhook_urls": ["https://test.com"]})
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_get_synonyms(admin_client):
    response = admin_client.get("/api/v1/admin/rules/synonyms")
    assert response.status_code == 200
    assert len(response.json()["synonyms"]) > 0

def test_add_synonym(admin_client):
    response = admin_client.post("/api/v1/admin/rules/synonyms", json={"term": "laptop", "synonyms": ["macbook", "pc"]})
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_delete_synonym(admin_client):
    response = admin_client.delete("/api/v1/admin/rules/synonyms/laptop")
    assert response.status_code == 200
    assert response.json()["success"] is True

def test_get_system_metrics(admin_client):
    response = admin_client.get("/api/v1/admin/system/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "cpu_percent" in data
    assert "ram_percent" in data
    assert "gpu_enabled" in data
    assert "gpu_name" in data

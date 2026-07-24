import pytest
from fastapi.testclient import TestClient

from app.api.dependencies import TenantContext
from app.mcp.context import get_mcp_tenant_context
from main import app

client = TestClient(app)

def test_mcp_sse_unauthorized():
    response = client.get("/api/v1/mcp/sse")
    assert response.status_code == 401

# In a real integration test, we would hit the DB to validate API keys.
# Since we might not have a running test DB here, we skip the DB part or use mocks.

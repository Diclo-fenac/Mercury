import sys
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.api.dependencies import get_container_dependency
from app.container import Container
from app.infrastructure.id_generator import IDGenerator
from main import app


class TestAdminAPIIntegration:
    """Integration tests for admin endpoints and onboarding lifecycle"""

    @pytest.fixture
    async def setup_client(self):
        """Initialize container with real services and setup async client"""
        from dotenv import load_dotenv
        load_dotenv()

        container = Container()
        await container.initialize()

        redis = container.get("redis")
        if redis:
            await redis.delete_matching("onboard:*")
            await redis.delete_matching("rate_limit:*")

        # Remove mock dependency overrides from app
        app.dependency_overrides.clear()
        
        # Override container dependency with the real test container
        app.dependency_overrides[get_container_dependency] = lambda: container

        # We do NOT override require_auth, get_tenant_context or require_admin_key
        # so that we test the actual resolution of API keys from the headers!

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            yield ac, container

        await container.cleanup()
        app.dependency_overrides.clear()

    @pytest.fixture
    def id_gen(self):
        return IDGenerator()

    @pytest.mark.asyncio
    async def test_admin_flow_and_onboarding(self, setup_client, id_gen):
        client, container = setup_client
        tenant_provisioner = container.get('tenant_provisioner')
        typesense_client = container.get('typesense')

        suffix = id_gen.timestamp()
        org_name = f"Admin Store {suffix}"
        org_slug = f"admin-store-{suffix}"
        owner_email = f"admin-{suffix}@example.com"

        # 1. Onboard Tenant
        onboard_payload = {
            "name": org_name,
            "slug": org_slug,
            "owner_email": owner_email,
            "plan": "free"
        }
        res_onboard = await client.post("/api/v1/admin/onboard", json=onboard_payload)
        if res_onboard.status_code != 201:
            print(f"ONBOARD FAILED: {res_onboard.text}")
        assert res_onboard.status_code == 201
        
        data = res_onboard.json()
        assert data["success"] is True
        org_id = data["organization"]["id"]
        admin_key = data["keys"]["admin_key"]
        search_key = data["keys"]["search_key"]

        # Check Typesense collection got provisioned
        collection_name = f"tenant_{org_id}_products"
        assert await typesense_client.collection_exists(collection_name) is True

        # 2. Get Config (using admin key)
        headers = {"X-API-Key": admin_key}
        res_get_cfg = await client.get("/api/v1/admin/config", headers=headers)
        assert res_get_cfg.status_code == 200
        cfg = res_get_cfg.json()
        assert cfg["out_of_stock_behavior"] == "demote"

        # Test unauthorized (no header or cookie)
        client.cookies.clear()
        res_unauth = await client.get("/api/v1/admin/config")
        assert res_unauth.status_code in (401, 422)  # unauthorized when credentials missing

        # Test invalid key
        res_invalid = await client.get("/api/v1/admin/config", headers={"X-API-Key": "invalid_key"})
        assert res_invalid.status_code == 401

        # Test forbidden (using public search key)
        res_forbidden = await client.get("/api/v1/admin/config", headers={"X-API-Key": search_key})
        assert res_forbidden.status_code == 403

        # 3. Update Config (using admin key)
        update_payload = {"out_of_stock_behavior": "hide"}
        res_patch_cfg = await client.patch("/api/v1/admin/config", json=update_payload, headers=headers)
        assert res_patch_cfg.status_code == 200
        assert res_patch_cfg.json()["success"] is True

        # Verify update
        res_get_cfg2 = await client.get("/api/v1/admin/config", headers=headers)
        assert res_get_cfg2.json()["out_of_stock_behavior"] == "hide"

        # 4. Generate Key
        key_payload = {
            "key_type": "public_search",
            "name": "Additional Search Key",
            "scopes": ["search"]
        }
        res_keygen = await client.post("/api/v1/admin/keys", json=key_payload, headers=headers)
        assert res_keygen.status_code == 200
        key_data = res_keygen.json()
        assert key_data["success"] is True
        assert key_data["api_key"].startswith("pk_")

        # 5. Add Synonym
        synonym_payload = {
            "term": "kicks",
            "synonyms": ["sneakers", "shoes"]
        }
        res_syn = await client.post("/api/v1/admin/synonyms", json=synonym_payload, headers=headers)
        assert res_syn.status_code == 200
        assert res_syn.json()["success"] is True

        # 6. Add Pinned Product
        pinned_payload = {
            "query_pattern": "sneakers",
            "product_id": f"prod_1_{suffix}",
            "position": 1
        }
        res_pin = await client.post("/api/v1/admin/pinned", json=pinned_payload, headers=headers)
        assert res_pin.status_code == 200
        assert res_pin.json()["success"] is True

        # 7. Get Analytics
        res_analytics = await client.get("/api/v1/admin/analytics", headers=headers)
        assert res_analytics.status_code == 200
        analytics_data = res_analytics.json()
        assert "total_queries" in analytics_data
        assert "zero_result_count" in analytics_data
        assert "average_latency_ms" in analytics_data
        assert "top_queries" in analytics_data

        # 7.2. Test Catalog Stats (initial empty/onboarded collection should exist)
        res_stats = await client.get("/api/v1/admin/catalog/stats", headers=headers)
        assert res_stats.status_code == 200
        stats_data = res_stats.json()
        assert stats_data["exists"] is True
        assert stats_data["product_count"] == 0

        # 7.3. Test Catalog Upload
        csv_data = (
            "id,title,description,brand,category,selling_price,rating,stock\n"
            f"prod_upload_1_{suffix},Super Shoe,A great running shoe,Nike,Shoes,120.0,4.5,true\n"
            f"prod_upload_2_{suffix},Awesome Cap,Stylish red cap,Adidas,Apparel,25.0,4.2,true\n"
        )
        files = {"file": ("catalog.csv", csv_data, "text/csv")}
        res_upload = await client.post("/api/v1/admin/catalog/upload", files=files, headers=headers)
        assert res_upload.status_code == 200
        upload_json = res_upload.json()
        assert upload_json["success"] is True
        assert upload_json["stats"]["indexed"] == 2

        # 7.4. Test Catalog Stats post-upload
        res_stats_after = await client.get("/api/v1/admin/catalog/stats", headers=headers)
        assert res_stats_after.status_code == 200
        assert res_stats_after.json()["product_count"] == 2

        # 7.5. Test Catalog Webhook (Single Upsert)
        webhook_upsert_payload = {
            "action": "upsert",
            "product": {
                "id": f"prod_webhook_{suffix}",
                "title": "Webhook Watch",
                "description": "Smart watch upserted via webhook",
                "brand": "Apple",
                "category": "Electronics",
                "selling_price": 399.0,
                "rating": 4.8,
                "stock": True
            }
        }
        res_webhook_ups = await client.post("/api/v1/admin/catalog/webhook", json=webhook_upsert_payload, headers=headers)
        assert res_webhook_ups.status_code == 200
        assert res_webhook_ups.json()["success"] is True
        
        # Verify stats increased to 3
        res_stats_webhook = await client.get("/api/v1/admin/catalog/stats", headers=headers)
        assert res_stats_webhook.json()["product_count"] == 3

        # 7.6. Test Catalog Webhook (Single Delete)
        webhook_delete_payload = {
            "action": "delete",
            "product": {
                "id": f"prod_webhook_{suffix}"
            }
        }
        res_webhook_del = await client.post("/api/v1/admin/catalog/webhook", json=webhook_delete_payload, headers=headers)
        assert res_webhook_del.status_code == 200
        assert res_webhook_del.json()["success"] is True

        # Verify stats decreased back to 2
        res_stats_final = await client.get("/api/v1/admin/catalog/stats", headers=headers)
        assert res_stats_final.json()["product_count"] == 2

        # 7.7. Test Widget Config Endpoint (with public search key)
        widget_headers = {"X-API-Key": search_key}
        res_widget_cfg = await client.get("/api/v1/widget/config", headers=widget_headers)
        assert res_widget_cfg.status_code == 200
        widget_cfg_data = res_widget_cfg.json()
        assert widget_cfg_data["success"] is True
        assert widget_cfg_data["config"]["widget_primary_color"] == "#6366f1"

        # 7.8. Test Widget Instant Search Endpoint (with public search key)
        res_instant = await client.get(
            "/api/v1/widget/search/instant",
            params={"q": "Super"},
            headers=widget_headers
        )
        assert res_instant.status_code == 200
        instant_data = res_instant.json()
        assert instant_data["success"] is True
        assert len(instant_data["suggestions"]) >= 1
        assert instant_data["suggestions"][0]["title"] == "Super Shoe"

        # 8. Clean up / Deprovision
        await tenant_provisioner.deprovision_tenant(org_id)
        assert await typesense_client.collection_exists(collection_name) is False

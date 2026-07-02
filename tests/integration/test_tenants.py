import pytest
import uuid
from pathlib import Path
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.container import Container
from app.infrastructure.id_generator import IDGenerator


class TestTenantIntegration:
    """Integration tests for SaaS Multi-Tenancy Layer"""

    @pytest.fixture
    async def container(self):
        """Initialize container with real services"""
        from dotenv import load_dotenv
        load_dotenv()

        container = Container()
        await container.initialize()
        yield container
        await container.cleanup()

    @pytest.fixture
    def id_gen(self):
        return IDGenerator()

    @pytest.mark.asyncio
    async def test_tenant_lifecycle_and_provisioning(self, container, id_gen):
        tenant_service = container.get('tenant_service')
        tenant_provisioner = container.get('tenant_provisioner')
        typesense_client = container.get('typesense')

        assert tenant_service is not None
        assert tenant_provisioner is not None

        # 1. Create Organization
        suffix = id_gen.timestamp()
        org_name = f"Test Shop {suffix}"
        org_slug = f"test-shop-{suffix}"
        owner_email = f"owner-{suffix}@example.com"

        org_dict = await tenant_service.create_organization(
            name=org_name,
            slug=org_slug,
            owner_email=owner_email,
            plan="free"
        )

        assert org_dict["id"] is not None
        assert org_dict["name"] == org_name
        assert org_dict["slug"] == org_slug
        org_id = org_dict["id"]

        # 2. Generate API Keys
        # Public search key
        pub_prefix, pub_key = await tenant_service.generate_api_key(
            org_id=org_id,
            key_type="public_search",
            name="Public Key",
            scopes=["search"]
        )
        assert pub_key.startswith("pk_")
        assert len(pub_key) > 20

        # Private admin key
        admin_prefix, admin_key = await tenant_service.generate_api_key(
            org_id=org_id,
            key_type="private_admin",
            name="Admin Key",
            scopes=["all"]
        )
        assert admin_key.startswith("sk_")

        # 3. Validate API Keys
        # Public search key validation
        pub_ctx = await tenant_service.validate_api_key(pub_key)
        assert pub_ctx is not None
        assert pub_ctx["organization_id"] == org_id
        assert pub_ctx["key_type"] == "public_search"
        assert "search" in pub_ctx["scopes"]
        assert pub_ctx["config"]["enable_semantic"] is True

        # Check caching by validating again (hits Redis if cache is enabled)
        pub_ctx_cached = await tenant_service.validate_api_key(pub_key)
        assert pub_ctx_cached == pub_ctx

        # Admin key validation
        admin_ctx = await tenant_service.validate_api_key(admin_key)
        assert admin_ctx is not None
        assert admin_ctx["key_type"] == "private_admin"

        # Invalid key validation
        invalid_ctx = await tenant_service.validate_api_key("pk_invalid_key_123")
        assert invalid_ctx is None

        # 4. Provision Tenant Typesense Collection
        # Check that collection doesn't exist yet
        collection_name = f"tenant_{org_id}_products"
        exists_before = await typesense_client.collection_exists(collection_name)
        assert exists_before is False

        # Provision
        provision_ok = await tenant_provisioner.provision_tenant(org_id, num_dim=384)
        assert provision_ok is True

        # Check exists
        exists_after = await typesense_client.collection_exists(collection_name)
        assert exists_after is True

        # 5. Usage Metering and Limit Enforcement
        # Fetch current limits (free plan has 10,000 limit)
        within_limit, remaining = await tenant_service.check_usage_limit(org_id)
        assert within_limit is True
        assert remaining == 10000

        # Record usage
        await tenant_service.record_usage(
            org_id=org_id,
            event_type="search_query",
            query_text="running shoes",
            latency_ms=12,
            result_count=5,
            api_key_id=pub_ctx["key_id"]
        )

        # Check limits again
        within_limit_after, remaining_after = await tenant_service.check_usage_limit(org_id)
        assert within_limit_after is True
        assert remaining_after == 9999

        # 6. Deprovision Collection
        deprovision_ok = await tenant_provisioner.deprovision_tenant(org_id)
        assert deprovision_ok is True

        exists_final = await typesense_client.collection_exists(collection_name)
        assert exists_final is False

    @pytest.mark.asyncio
    async def test_tenant_aware_search_orchestration(self, container, id_gen):
        tenant_service = container.get('tenant_service')
        tenant_provisioner = container.get('tenant_provisioner')
        search_orchestrator = container.get('search_orchestrator')
        typesense_client = container.get('typesense')
        postgres_client = container.get('postgres')

        suffix = id_gen.timestamp()
        org_slug = f"search-shop-{suffix}"
        
        # 1. Create Organization
        org_dict = await tenant_service.create_organization(
            name=f"Search Shop {suffix}",
            slug=org_slug,
            owner_email=f"search-{suffix}@example.com"
        )
        org_id = org_dict["id"]
        collection_name = f"tenant_{org_id}_products"

        # 2. Provision Typesense collection
        await tenant_provisioner.provision_tenant(org_id)

        # 3. Seed products into PostgreSQL
        from app.infrastructure.db.models import Product
        import uuid
        
        prod_a_id = f"prod_a_{suffix}"
        prod_b_id = f"prod_b_{suffix}"

        async with postgres_client.async_session() as session:
            p_a = Product(
                id=prod_a_id,
                name="Red Sports Sneakers",
                title="Red Sports Sneakers",
                brand="Nike",
                category="Shoes",
                rating=4.5,
                stock=True,
                online_available=True,
                price={"selling": 120.0}
            )
            p_b = Product(
                id=prod_b_id,
                name="Blue Running Shoes",
                title="Blue Running Shoes",
                brand="Adidas",
                category="Shoes",
                rating=4.0,
                stock=False, # Out of stock
                online_available=True,
                price={"selling": 90.0}
            )
            session.add(p_a)
            session.add(p_b)
            await session.commit()

        # 4. Generate local embeddings and seed into Typesense
        local_embedder = container.get('embeddings')
        emb_a = await local_embedder.embed_text("Red Sports Sneakers Nike Shoes")
        emb_b = await local_embedder.embed_text("Blue Running Shoes Adidas Shoes")

        doc_a = {
            "id": prod_a_id,
            "name": "Red Sports Sneakers",
            "title": "Red Sports Sneakers",
            "brand": "Nike",
            "category": "Shoes",
            "sub_category": "",
            "description": "Nike running trainers",
            "rating": 4.5,
            "stock": True,
            "online_available": True,
            "selling_price": 120.0,
            "embedding": emb_a
        }
        doc_b = {
            "id": prod_b_id,
            "name": "Blue Running Shoes",
            "title": "Blue Running Shoes",
            "brand": "Adidas",
            "category": "Shoes",
            "sub_category": "",
            "description": "Adidas running trainers",
            "rating": 4.0,
            "stock": False,
            "online_available": True,
            "selling_price": 90.0,
            "embedding": emb_b
        }

        await typesense_client.index_documents(collection_name, [doc_a, doc_b])

        # 5. Resolve TenantContext
        _, raw_key = await tenant_service.generate_api_key(org_id, "public_search", "Test Search Key")
        ctx_dict = await tenant_service.validate_api_key(raw_key)
        
        from app.api.dependencies import TenantContext
        tenant_ctx = TenantContext(
            organization_id=org_id,
            organization_slug=org_slug,
            key_type=ctx_dict["key_type"],
            scopes=ctx_dict["scopes"],
            plan=ctx_dict["plan"],
            config=ctx_dict["config"],
            collection_name=collection_name
        )

        # 6. Test basic search (should return both products)
        res = await search_orchestrator.handle(
            query="Sneakers",
            user_id="test_user",
            tenant_context=tenant_ctx
        )
        assert res["success"] is True
        product_ids = [p["id"] for p in res["results"]]
        assert prod_a_id in product_ids
        assert prod_b_id in product_ids

        # 7. Test Synonym Expansion
        # Add synonym: sneakers -> kicks
        async with tenant_service.db.async_session() as session:
            from app.domain.tenants.models import Synonym
            syn = Synonym(
                organization_id=uuid.UUID(org_id),
                term="kicks",
                synonyms=["sneakers", "trainers"],
                is_active=True
            )
            session.add(syn)
            await session.commit()

        # Query "kicks"
        res_syn = await search_orchestrator.handle(
            query="kicks",
            user_id="test_user",
            tenant_context=tenant_ctx
        )
        assert res_syn["success"] is True
        assert len(res_syn["results"]) > 0

        # 8. Test Merchandising Pinned Products
        # Pin Product B (Adidas) to rank #1
        async with tenant_service.db.async_session() as session:
            from app.domain.tenants.models import PinnedProduct
            pin = PinnedProduct(
                organization_id=uuid.UUID(org_id),
                query_pattern="sneakers",
                product_id=prod_b_id,
                position=1,
                is_active=True
            )
            session.add(pin)
            await session.commit()

        # Clear cache to avoid getting cached results from step 6
        if container.get('redis'):
            await container.get('redis')._client.flushdb()

        res_pinned = await search_orchestrator.handle(
            query="Sneakers",
            user_id="test_user",
            tenant_context=tenant_ctx
        )
        assert res_pinned["success"] is True
        # Product B should be rank 1 (index 0)
        assert res_pinned["results"][0]["id"] == prod_b_id

        # 9. Test Out-of-Stock behavior (hide)
        # Update config to out_of_stock_behavior = "hide"
        await tenant_service.update_config(org_id, out_of_stock_behavior="hide")
        
        # Resolve context again to get updated config
        ctx_dict_updated = await tenant_service.validate_api_key(raw_key)
        tenant_ctx_hide = TenantContext(
            organization_id=org_id,
            organization_slug=org_slug,
            key_type=ctx_dict_updated["key_type"],
            scopes=ctx_dict_updated["scopes"],
            plan=ctx_dict_updated["plan"],
            config=ctx_dict_updated["config"],
            collection_name=collection_name
        )

        # Clear cache to get updated out-of-stock config
        if container.get('redis'):
            await container.get('redis')._client.flushdb()

        res_hidden = await search_orchestrator.handle(
            query="Sneakers",
            user_id="test_user",
            tenant_context=tenant_ctx_hide
        )
        assert res_hidden["success"] is True
        # Should only contain prod_a (prod_b is out of stock and hidden)
        ids_hidden = [p["id"] for p in res_hidden["results"]]
        assert prod_a_id in ids_hidden
        assert prod_b_id not in ids_hidden

        # 10. Clean up
        await tenant_provisioner.deprovision_tenant(org_id)


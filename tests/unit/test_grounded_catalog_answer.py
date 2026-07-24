from dataclasses import dataclass

import pytest

from app.intelligence.engine import LLMEngine


@dataclass
class Tenant:
    organization_id: str = "tenant-1"
    organization_slug: str = "mercury-shop"


@pytest.mark.asyncio
async def test_catalog_answer_uses_read_only_retrieval_and_verified_citations():
    engine = LLMEngine(api_key="mock")
    calls = []

    async def search_products(query, limit):
        calls.append((query, limit))
        return [
            {
                "id": "sku-1",
                "title": "Mercury Shoe",
                "selling_price": 49.99,
                "stock": True,
                "online_available": True,
                "url": "https://merchant.example/products/sku-1",
                "description": "Running shoe",
                "brand": "Mercury",
                "category": "Shoes",
                "breakdown": {"retrieval": {"rrf_score": 0.03}},
            }
        ]

    engine.register_tool("search_products", search_products, "search", {})

    result = await engine.generate_with_tools("need shoes", tenant_context=Tenant())

    assert calls == [("need shoes", 5)]
    assert result["function_called"] == "search_products"
    assert "[sku-1]" in result["response"]
    assert result["citations"] == [
        {
            "product_id": "sku-1",
            "product_url": "https://merchant.example/products/sku-1",
            "price": 49.99,
            "availability": "in_stock",
            "merchant": "mercury-shop",
            "confidence_score": 0.03,
            "source_evidence": {
                "title": "Mercury Shoe",
                "brand": "Mercury",
                "category": "Shoes",
                "description": "Running shoe",
            },
        }
    ]


@pytest.mark.asyncio
async def test_catalog_answer_refuses_to_invent_results_when_retrieval_empty():
    engine = LLMEngine(api_key="mock")

    async def search_products(query, limit):
        return []

    engine.register_tool("search_products", search_products, "search", {})

    result = await engine.generate_with_tools("need shoes", tenant_context=Tenant())

    assert result["response"] == "I couldn't find matching products in this store."
    assert result["citations"] == []

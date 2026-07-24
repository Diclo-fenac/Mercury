from app.infrastructure.cache.keys import build_search_cache_key, canonical_json


def test_canonical_json_is_stable_for_equivalent_mappings():
    first = {"brand": ["Mercury"], "price": {"max": 100, "min": 10}}
    second = {"price": {"min": 10, "max": 100}, "brand": ["Mercury"]}

    assert canonical_json(first) == canonical_json(second)


def test_search_cache_key_is_opaque_and_tenant_isolated():
    common = {
        "query": "running shoes",
        "user_id": "user-123",
        "filters": {"brand": ["Mercury"]},
        "limit": 20,
        "offset": 0,
        "sort": {"field": "price", "direction": "asc"},
        "search_type": "hybrid",
        "include_suggestions": False,
        "collection": "tenant_products",
        "revision": 4,
    }

    first = build_search_cache_key(tenant_id="tenant-a", **common)
    reordered_filters = build_search_cache_key(
        tenant_id="tenant-a",
        **{**common, "filters": {"brand": ["Mercury"]}},
    )
    other_tenant = build_search_cache_key(tenant_id="tenant-b", **common)

    assert first == reordered_filters
    assert first != other_tenant
    assert "running shoes" not in first
    assert "user-123" not in first


def test_search_cache_key_separates_response_shaping_inputs():
    common = {
        "tenant_id": "tenant-a",
        "query": "running shoes",
        "user_id": "user-123",
        "filters": {},
        "limit": 20,
        "offset": 0,
        "sort": None,
        "search_type": "hybrid",
        "include_suggestions": False,
        "collection": "tenant_products",
        "revision": 1,
    }
    baseline = build_search_cache_key(**common)

    assert baseline != build_search_cache_key(**{**common, "offset": 20})
    assert baseline != build_search_cache_key(**{**common, "sort": {"field": "price"}})
    assert baseline != build_search_cache_key(**{**common, "search_type": "keyword"})
    assert baseline != build_search_cache_key(**{**common, "revision": 2})

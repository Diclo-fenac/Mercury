"""Deterministic, opaque Redis cache-key builders.

Cache keys are infrastructure details. They must not leak query text, user IDs, or
credential material while still separating every input that can change a response.
"""

import json
from collections.abc import Mapping
from datetime import date, datetime
from enum import Enum
from hashlib import sha256
from typing import Any, Optional
from uuid import UUID

CACHE_KEY_PREFIX = "mercury"
CACHE_KEY_VERSION = "v1"


def _normalize(value: Any) -> Any:
    """Convert supported values into a deterministic JSON-compatible structure."""
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _normalize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_normalize(item) for item in value]
    if isinstance(value, (set, frozenset)):
        normalized = [_normalize(item) for item in value]
        return sorted(normalized, key=lambda item: json.dumps(item, sort_keys=True, default=str))
    if isinstance(value, (date, datetime, UUID)):
        return str(value)
    if isinstance(value, Enum):
        return _normalize(value.value)
    if hasattr(value, "model_dump"):
        return _normalize(value.model_dump())
    if hasattr(value, "dict"):
        return _normalize(value.dict())
    return str(value)


def canonical_json(payload: Any) -> str:
    """Serialize a value consistently so equivalent requests produce one key."""
    return json.dumps(_normalize(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _digest(payload: Any) -> str:
    return sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def build_cache_key(namespace: str, payload: Any, tenant_id: Optional[str] = None) -> str:
    """Build an opaque cache key with an optional tenant-specific partition."""
    namespace_part = namespace.strip().replace(" ", "-")
    parts = [CACHE_KEY_PREFIX, CACHE_KEY_VERSION, namespace_part]
    if tenant_id:
        parts.append(f"t-{_digest({'tenant_id': str(tenant_id)})[:16]}")
    parts.append(_digest(payload))
    return ":".join(parts)


def build_search_cache_key(
    *,
    tenant_id: Optional[str],
    query: str,
    user_id: Optional[str],
    filters: Optional[Mapping[str, Any]],
    limit: int,
    offset: int,
    sort: Optional[Mapping[str, Any]],
    search_type: str,
    include_suggestions: bool,
    collection: str,
    revision: int,
) -> str:
    """Build a key for every input capable of changing a search response."""
    return build_cache_key(
        "search",
        {
            "query": query,
            "user_id": user_id,
            "filters": filters or {},
            "limit": limit,
            "offset": offset,
            "sort": sort or {},
            "search_type": search_type,
            "include_suggestions": include_suggestions,
            "collection": collection,
            "revision": revision,
        },
        tenant_id=tenant_id,
    )


def build_user_profile_cache_key(tenant_id: str, user_id: str) -> str:
    """Build opaque cache key for one merchant-local customer profile."""
    return build_cache_key("user-profile", {"user_id": user_id}, tenant_id=tenant_id)


def build_user_context_cache_key(tenant_id: str, user_id: str) -> str:
    """Build opaque cache key for one merchant-local short-term AI context."""
    return build_cache_key("user-context", {"user_id": user_id}, tenant_id=tenant_id)


def build_image_cache_key(tenant_id: str, image_id: str, record_type: str = "analysis") -> str:
    """Build an opaque tenant-local key for temporary uploaded-image metadata."""
    return build_cache_key(
        "image",
        {"image_id": image_id, "record_type": record_type},
        tenant_id=tenant_id,
    )


def tenant_context_cache_key(api_key_hash: str) -> str:
    """Build a cache key for an already-hashed API key without exposing that hash."""
    return build_cache_key("tenant-context", {"api_key_hash": api_key_hash})


def tenant_context_membership_key(tenant_id: str) -> str:
    """Build the tenant-local set used for targeted tenant-context invalidation."""
    return build_cache_key("tenant-context-members", {"membership": True}, tenant_id=tenant_id)


def tenant_namespace_revision_key(tenant_id: str, namespace: str) -> str:
    """Build the persistent logical-invalidation revision key for a tenant namespace."""
    return build_cache_key("namespace-revision", {"namespace": namespace}, tenant_id=tenant_id)

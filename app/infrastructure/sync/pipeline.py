"""
Sync Pipeline - Postgres → Typesense
Builds product text, generates Gemini embedding, upserts to the search store.
"""
from typing import Any, Dict

from app.utils.logger import get_logger

logger = get_logger("sync_pipeline")

# Typesense collection schema (created on first sync if missing)
TYPESENSE_SCHEMA = {
    "name": "products",
    "fields": [
        {"name": "id", "type": "string"},
        {"name": "name", "type": "string", "optional": True},
        {"name": "title", "type": "string", "optional": True},
        {"name": "brand", "type": "string", "optional": True, "facet": True},
        {"name": "category", "type": "string", "optional": True, "facet": True},
        {"name": "sub_category", "type": "string", "optional": True, "facet": True},
        {"name": "description", "type": "string", "optional": True},
        {"name": "rating", "type": "float"},          # required — used as default_sorting_field
        {"name": "stock", "type": "bool", "optional": True},
        {"name": "online_available", "type": "bool", "optional": True},
        {"name": "selling_price", "type": "float", "optional": True},
        {"name": "embedding", "type": "float[]", "num_dim": 384, "optional": True},  # 384 dimensions for all-MiniLM-L6-v2
        {"name": "image_vector", "type": "float[]", "num_dim": 512, "optional": True},
    ],
    "default_sorting_field": "rating",
}


def _build_product_text(product: Dict[str, Any]) -> str:
    """Build a rich text string from product fields for embedding."""
    parts = []
    for field in ("title", "name", "description", "brand", "category", "sub_category"):
        val = product.get(field)
        if val:
            parts.append(str(val))

    tags = product.get("tags") or {}
    if isinstance(tags, dict):
        for k, v in tags.items():
            if v:
                parts.append(f"{k}: {v}")

    return " ".join(parts)


def _product_to_typesense_doc(product: Dict[str, Any]) -> Dict[str, Any]:
    """Convert product dict to a flat Typesense document."""
    price = product.get("price") or {}
    selling_price = float(price.get("selling", 0)) if isinstance(price, dict) else float(price or 0)

    return {
        "id": str(product["id"]),
        "name": product.get("name") or "",
        "title": product.get("title") or "",
        "brand": product.get("brand") or "",
        "category": product.get("category") or "",
        "sub_category": product.get("sub_category") or "",
        "description": product.get("description") or "",
        "rating": float(product.get("rating") or 0),
        "stock": bool(product.get("stock")),
        "online_available": bool(product.get("online_available", True)),
        "selling_price": selling_price,
    }

class SyncPipeline:
    """
    Syncs a single product from Postgres into Typesense (vector + keyword).
    Designed to be called from SQLAlchemy event listeners after insert/update.
    """

    def __init__(self, embeddings, typesense, collection_name: str = "products"):
        self.embeddings = embeddings          # GeminiEmbeddings / LocalEmbedder
        self.typesense = typesense            # TypesenseClient
        self.collection_name = collection_name
        self._ts_schema_ensured = False

    async def _ensure_typesense_collection(self) -> None:
        if self._ts_schema_ensured:
            return
        if not await self.typesense.collection_exists(self.collection_name):
            ok = await self.typesense.create_collection(TYPESENSE_SCHEMA)
            if not ok:
                return  # don't set flag — retry next time
        self._ts_schema_ensured = True

    async def sync_product(self, product: Dict[str, Any]) -> bool:
        """
        Full sync for one product:
          1. Build text → embed
          2. Upsert document with embedding to Typesense
        Returns True if successful.
        """
        product_id = product.get("id")
        if not product_id:
            logger.warning("sync_product called with no product id, skipping")
            return False

        text = _build_product_text(product)
        if not text.strip():
            logger.warning(f"No text to embed for product {product_id}, skipping")
            return False

        # 1. Generate embedding
        vector = await self.embeddings.embed_text(text, task_type="retrieval_document")
        if not vector:
            logger.error(f"Failed to generate embedding for product {product_id}")
            return False

        # 2. Upsert to Typesense
        ts_ok = False
        if self.typesense and self.typesense._connected:
            await self._ensure_typesense_collection()
            doc = _product_to_typesense_doc(product)
            doc["embedding"] = vector
            result = await self.typesense.index_documents(
                self.collection_name, [doc]
            )
            ts_ok = result.get("success", False)
        else:
            logger.warning("Typesense not connected, skipping keyword upsert")

        if ts_ok:
            logger.info(
                f"Synced product {product_id} to Typesense with vector"
            )

        return ts_ok

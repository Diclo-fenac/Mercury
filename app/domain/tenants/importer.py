"""
Catalog Importer - Layer 5: Domain
Parses uploaded catalog files (CSV/JSON), generates local embeddings in batch, and indexes into Typesense.
"""
import csv
import io
import uuid
from typing import Any, Dict, List
from app.infrastructure.search.typesense import TypesenseClient
from app.utils.logger import get_logger

logger = get_logger("catalog_importer")


class CatalogImporter:
    """Handles bulk parsing, embedding generation, and indexing of tenant catalogs"""

    def __init__(self, typesense: TypesenseClient, embeddings):
        self.typesense = typesense
        self.embeddings = embeddings

    async def import_csv(self, org_id: str, csv_content: str) -> Dict[str, Any]:
        """
        Parse CSV content, generate local embeddings, and bulk index to Typesense.
        """
        collection_name = f"tenant_{org_id}_products"
        
        # 1. Parse CSV
        f = io.StringIO(csv_content.strip())
        reader = csv.DictReader(f)
        
        docs = []
        for i, row in enumerate(reader):
            docs.append(self._normalize_product(row, i))
            
        return await self._process_and_index(collection_name, docs)

    async def import_json(self, org_id: str, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Parse JSON array, generate local embeddings, and bulk index to Typesense.
        """
        collection_name = f"tenant_{org_id}_products"
        
        docs = []
        for i, row in enumerate(products):
            docs.append(self._normalize_product(row, i))
            
        return await self._process_and_index(collection_name, docs)

    def _normalize_product(self, row: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Normalize a single product dict"""
        prod_id = row.get("id") or row.get("product_id") or f"prod_{index}_{uuid.uuid4().hex[:8]}"
        
        # Map columns and normalize types based on tenant product schema
        title = row.get("title") or row.get("name") or ""
        name = row.get("name") or row.get("title") or ""
        brand = row.get("brand") or "Unknown"
        category = row.get("category") or "General"
        sub_category = row.get("sub_category") or ""
        description = row.get("description") or ""
        
        # Price
        try:
            price_val = row.get("selling_price") or row.get("price") or "0"
            selling_price = float(price_val)
        except (ValueError, TypeError):
            selling_price = 0.0
            
        # Rating
        try:
            rating_val = row.get("rating") or "0.0"
            rating = float(rating_val)
        except (ValueError, TypeError):
            rating = 0.0
            
        # Stock & Availability
        stock_str = str(row.get("stock", "true")).lower()
        stock = stock_str in ("true", "1", "yes", "in_stock")
        
        online_str = str(row.get("online_available", "true")).lower()
        online_available = online_str in ("true", "1", "yes", "available")
        
        return {
            "id": str(prod_id),
            "name": str(name),
            "title": str(title),
            "brand": str(brand),
            "category": str(category),
            "sub_category": str(sub_category),
            "description": str(description),
            "rating": rating,
            "stock": stock,
            "online_available": online_available,
            "selling_price": selling_price,
        }

    async def _process_and_index(self, collection_name: str, docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate embeddings and index to Typesense"""
        if not docs:
            return {"success": True, "total": 0, "indexed": 0, "errors": 0}

        # 2. Construct text strings for batch embedding
        texts = []
        for doc in docs:
            parts = []
            for field in ("title", "name", "description", "brand", "category", "sub_category"):
                val = doc.get(field)
                if val:
                    parts.append(val)
            texts.append(" ".join(parts))
            
        # 3. Generate local embeddings
        try:
            vectors = await self.embeddings.embed_batch(texts)
            for doc, vector in zip(docs, vectors):
                doc["embedding"] = vector or [0.0] * 384
        except Exception as e:
            logger.error(f"Failed to generate embeddings in batch: {e}")
            return {
                "success": False,
                "total": len(docs),
                "indexed": 0,
                "errors": len(docs),
                "detail": f"Embedding generation failed: {str(e)}"
            }

        # 4. Bulk index to Typesense in batches
        batch_size = 50
        indexed_count = 0
        error_count = 0
        
        for i in range(0, len(docs), batch_size):
            batch = docs[i:i + batch_size]
            try:
                res = await self.typesense.index_documents(collection_name, batch)
                if res.get("success", False):
                    indexed_count += len(batch)
                else:
                    error_count += len(batch)
                    logger.error(f"Error indexing batch: {res.get('error')}")
            except Exception as e:
                error_count += len(batch)
                logger.error(f"Exception indexing batch: {e}")
                
        return {
            "success": error_count == 0,
            "total": len(docs),
            "indexed": indexed_count,
            "errors": error_count
        }

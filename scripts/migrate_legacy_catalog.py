"""Migrate the legacy global product catalog into one tenant catalog.

PostgreSQL remains canonical. The global Typesense collection is read-only input
for the derived tenant index; it is never used as a cross-tenant API collection.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List

from sqlalchemy import func, select

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.domain.tenants.provisioning import TenantProvisioner
from app.infrastructure.catalog.repository import CatalogRepository
from app.infrastructure.db.models import Product
from app.infrastructure.db.postgres import PostgresClient
from app.infrastructure.search.typesense import TypesenseClient
from app.settings import get_settings


def _legacy_document(product: Product) -> Dict[str, Any]:
    """Convert one legacy ORM row into a JSON-safe canonical document."""
    title = product.title or product.name or str(product.id)
    return {
        "id": str(product.id),
        "name": product.name or title,
        "title": title,
        "brand": product.brand or "",
        "category": product.category or "",
        "sub_category": product.sub_category or "",
        "description": product.description or "",
        "url": product.url,
        "price": product.price or {},
        "tags": product.tags or {},
        "images": product.images or [],
        "availability": product.availability or [],
        "metadata": product.extra_data or {},
        "rating": float(product.rating or 0),
        "stock": int(product.stock or 0),
        "online_available": bool(product.online_available),
        "seller_id": product.seller_id,
    }


async def _fetch_legacy_batch(db: PostgresClient, offset: int, limit: int) -> List[Dict[str, Any]]:
    async with db.async_session() as session:
        result = await session.scalars(
            select(Product).order_by(Product.id).offset(offset).limit(limit)
        )
        return [_legacy_document(product) for product in result.all()]


def _typesense_documents(source_export: str) -> List[Dict[str, Any]]:
    documents = []
    for line in source_export.splitlines():
        if line.strip():
            documents.append(json.loads(line))
    return documents


def _search_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Keep only fields accepted by the tenant search schema."""
    return {
        key: document[key]
        for key in (
            "id",
            "name",
            "title",
            "brand",
            "category",
            "sub_category",
            "description",
            "rating",
            "stock",
            "online_available",
            "selling_price",
        )
        if key in document
    }


async def _run(args: argparse.Namespace) -> None:
    settings = get_settings()
    db = PostgresClient(database_url=settings.DATABASE_URL)
    typesense = TypesenseClient(
        host=settings.TYPESENSE_HOST,
        port=settings.TYPESENSE_PORT,
        api_key=settings.TYPESENSE_API_KEY,
    )
    await db.connect()
    await typesense.connect()

    target_collection = f"tenant_{args.organization_id}_products"
    try:
        async with db.async_session() as session:
            legacy_total = int((await session.execute(select(func.count()).select_from(Product))).scalar_one())

        source_meta = await asyncio.get_running_loop().run_in_executor(
            None, lambda: typesense.client.collections[args.source_collection].retrieve()
        )
        source_export = await asyncio.get_running_loop().run_in_executor(
            None, lambda: typesense.client.collections[args.source_collection].documents.export()
        )
        source_documents = _typesense_documents(source_export)
        if len(source_documents) != int(source_meta.get("num_documents", -1)):
            raise RuntimeError(
                f"Source export count mismatch: metadata={source_meta.get('num_documents')} "
                f"exported={len(source_documents)}"
            )
        if len(source_documents) != legacy_total:
            raise RuntimeError(
                f"Legacy PostgreSQL/Typesense mismatch: postgres={legacy_total} "
                f"typesense={len(source_documents)}"
            )

        if not await typesense.collection_exists(target_collection):
            schema = TenantProvisioner(typesense).build_schema(target_collection, num_dim=384)
            if not await typesense.create_collection(schema):
                raise RuntimeError(f"Could not create {target_collection}")

        target_meta = await asyncio.get_running_loop().run_in_executor(
            None, lambda: typesense.client.collections[target_collection].retrieve()
        )
        target_count = int(target_meta.get("num_documents", 0))
        target_embedding = next(
            (field for field in target_meta.get("fields", []) if field.get("name") == "embedding"),
            {},
        )
        if target_count == 0 and not target_embedding.get("optional", False):
            if not args.recreate_empty_target:
                raise RuntimeError(
                    f"{target_collection} requires embeddings. Re-run with --recreate-empty-target "
                    "to recreate this verified-empty collection with optional vectors."
                )
            await asyncio.get_running_loop().run_in_executor(
                None, lambda: typesense.client.collections[target_collection].delete()
            )
            schema = TenantProvisioner(typesense).build_schema(target_collection, num_dim=384)
            if not await typesense.create_collection(schema):
                raise RuntimeError(f"Could not recreate {target_collection}")

        repository = CatalogRepository(db)
        catalog_id = await repository.ensure_default_product_catalog(args.organization_id)
        source_by_id = {str(document["id"]): _search_document(document) for document in source_documents}

        migrated = 0
        indexed = 0
        batch_size = args.batch_size
        for offset in range(0, legacy_total, batch_size):
            canonical_batch = await _fetch_legacy_batch(db, offset, batch_size)
            if not canonical_batch:
                break
            persisted = await repository.upsert_products(
                args.organization_id, catalog_id, canonical_batch
            )
            search_batch = [source_by_id[document["id"]] for document in canonical_batch]
            index_result = await typesense.index_documents(target_collection, search_batch)
            result_rows = index_result.get("results") or []
            outcomes = []
            for index, document in enumerate(persisted):
                detail = result_rows[index] if index < len(result_rows) else {}
                success = bool(detail.get("success", index_result.get("success", False)))
                outcomes.append(
                    {
                        "event_id": document["index_event_id"],
                        "success": success,
                        "error": detail.get("error") or index_result.get("error"),
                    }
                )
            await repository.record_index_results(outcomes)
            migrated += len(canonical_batch)
            indexed += sum(bool(outcome["success"]) for outcome in outcomes)
            print(f"processed={migrated}/{legacy_total} indexed={indexed}", flush=True)

        print(
            json.dumps(
                {
                    "organization_id": args.organization_id,
                    "catalog_id": catalog_id,
                    "source_collection": args.source_collection,
                    "target_collection": target_collection,
                    "legacy_products": legacy_total,
                    "canonical_upserted": migrated,
                    "typesense_indexed": indexed,
                },
                indent=2,
            )
        )
    finally:
        await typesense.close()
        await db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--organization-id", required=True)
    parser.add_argument("--source-collection", default="products")
    parser.add_argument("--batch-size", type=int, default=500)
    parser.add_argument("--recreate-empty-target", action="store_true")
    asyncio.run(_run(parser.parse_args()))


if __name__ == "__main__":
    main()

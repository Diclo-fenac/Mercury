#!/usr/bin/env python3
"""
Typesense-only sync: Postgres → Typesense (no embeddings needed)
Usage: python scripts/sync_typesense.py [--batch 100] [--offset 0]
"""
import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import func, select

from app.infrastructure.db.models import Product
from app.infrastructure.db.postgres import PostgresClient
from app.infrastructure.search.typesense import TypesenseClient
from app.infrastructure.sync.pipeline import TYPESENSE_SCHEMA, _product_to_typesense_doc
from app.settings import get_settings


async def fetch_batch(pg, offset, limit):
    async with pg.async_session() as session:
        rows = await session.execute(
            select(Product).order_by(Product.id).offset(offset).limit(limit)
        )
        return [pg._product_to_dict(p) for p in rows.scalars().all()]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int, default=100)
    parser.add_argument("--offset", type=int, default=0)
    args = parser.parse_args()

    s = get_settings()
    pg = PostgresClient(database_url=s.DATABASE_URL)
    ts = TypesenseClient(host=s.TYPESENSE_HOST, port=s.TYPESENSE_PORT, api_key=s.TYPESENSE_API_KEY)

    await pg.connect()
    await ts.connect()

    # Ensure collection exists
    if not await ts.collection_exists("products"):
        await ts.create_collection(TYPESENSE_SCHEMA)
        print("Created Typesense collection")

    async with pg.async_session() as session:
        total = (await session.execute(select(func.count()).select_from(Product))).scalar_one()

    print(f"Total products: {total} | batch: {args.batch} | start offset: {args.offset}\n")

    offset, synced, failed = args.offset, 0, 0
    while offset < total:
        batch = await fetch_batch(pg, offset, args.batch)
        if not batch:
            break

        docs = [_product_to_typesense_doc(p) for p in batch]
        result = await ts.index_documents("products", docs)

        if result.get("success"):
            synced += result.get("indexed", 0)
        else:
            failed += len(docs)

        offset += len(batch)
        print(f"  offset={offset}/{total}  synced={synced}  failed={failed}")

    print(f"\nDone. synced={synced}  failed={failed}")
    await pg.close()


if __name__ == "__main__":
    asyncio.run(main())

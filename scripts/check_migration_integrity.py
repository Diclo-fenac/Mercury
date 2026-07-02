"""
Post-migration integrity checks:
1. Barcode pids all resolve to a product
2. Product availability store_ids all exist in stores table
Run after remap_barcode_pids.py
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from app.infrastructure.db.postgres import PostgresClient
from app.settings import get_settings


async def check(postgres: PostgresClient) -> None:
    async with postgres.async_session() as session:
        # 1. Barcodes with unresolved pid
        result = await session.execute(text("""
            SELECT COUNT(*) FROM barcodes b
            WHERE b.pid IS NOT NULL
              AND NOT EXISTS (SELECT 1 FROM products p WHERE p.id = b.pid)
        """))
        broken_barcodes = result.scalar()
        print(f"{'✅' if broken_barcodes == 0 else '❌'} Barcodes with broken pid: {broken_barcodes}")

        # 2. Availability store_ids not in stores table
        result = await session.execute(text("""
            SELECT COUNT(DISTINCT avail->>'store_id') FROM products,
            jsonb_array_elements(availability) AS avail
            WHERE NOT EXISTS (
                SELECT 1 FROM stores s WHERE s.id = avail->>'store_id'
            )
        """))
        missing_stores = result.scalar()
        print(f"{'✅' if missing_stores == 0 else '⚠️ '} Availability entries referencing missing stores: {missing_stores}")

        # 3. Row counts
        for table in ('products', 'stores', 'barcodes', 'users'):
            r = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
            print(f"   {table}: {r.scalar()} rows")


async def main():
    settings = get_settings()
    postgres = PostgresClient(database_url=settings.DATABASE_URL)
    await postgres.connect()
    print("🔍 Running integrity checks...\n")
    await check(postgres)
    await postgres.close()


if __name__ == "__main__":
    asyncio.run(main())

"""
Remap barcodes.pid from original pid to new UUID v7 product ids.
Run this after migration completes.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update, text
from app.infrastructure.db.postgres import PostgresClient
from app.settings import get_settings


async def remap_barcode_pids(postgres: PostgresClient) -> None:
    async with postgres.async_session() as session:
        # Build original_pid -> new uuid7 id mapping from products.metadata
        rows = await session.execute(
            text("SELECT id, metadata->>'original_pid' AS original_pid FROM products WHERE metadata->>'original_pid' IS NOT NULL")
        )
        pid_map = {row.original_pid: row.id for row in rows}

    if not pid_map:
        print("⚠️  No original_pid entries found in products.metadata — nothing to remap.")
        return

    print(f"Found {len(pid_map)} product pid mappings")

    updated = 0
    skipped = 0

    async with postgres.async_session() as session:
        rows = await session.execute(text("SELECT id, pid FROM barcodes"))
        barcodes = rows.fetchall()

    for barcode_id, old_pid in barcodes:
        new_pid = pid_map.get(old_pid)
        if not new_pid:
            skipped += 1
            continue
        async with postgres.async_session() as session:
            await session.execute(
                text("UPDATE barcodes SET pid = :new_pid WHERE id = :barcode_id"),
                {"new_pid": new_pid, "barcode_id": barcode_id}
            )
            await session.commit()
        updated += 1

    print(f"✅ Remapped {updated} barcodes, {skipped} skipped (no matching product)")


async def main():
    settings = get_settings()
    postgres = PostgresClient(database_url=settings.DATABASE_URL)
    await postgres.connect()

    print("🔄 Remapping barcode pids...")
    await remap_barcode_pids(postgres)

    await postgres.close()
    print("✅ Done")


if __name__ == "__main__":
    asyncio.run(main())

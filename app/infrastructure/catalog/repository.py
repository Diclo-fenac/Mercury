"""PostgreSQL persistence for canonical catalogs and durable index events."""
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List
from uuid import UUID

from sqlalchemy import and_, or_, select

from app.domain.tenants.models import (
    Catalog,
    CatalogIndexEvent,
    CatalogItem,
    MerchantStore,
    Organization,
)
from app.infrastructure.db.postgres import PostgresClient

DEFAULT_STORE_SLUG = "default-store"
DEFAULT_CATALOG_SLUG = "default-products"


class CatalogRepository:
    """Owns transactional canonical catalog writes; Typesense is intentionally absent."""

    def __init__(
        self,
        db: PostgresClient,
        *,
        max_index_attempts: int = 10,
        processing_lease_seconds: int = 60,
    ):
        self.db = db
        self.max_index_attempts = max_index_attempts
        self.processing_lease_seconds = processing_lease_seconds

    async def ensure_default_product_catalog(self, organization_id: str) -> str:
        org_id = UUID(str(organization_id))
        async with self.db.async_session() as session:
            organization = await session.scalar(
                select(Organization).where(Organization.id == org_id).with_for_update()
            )
            if not organization:
                raise ValueError("Organization does not exist")

            catalog = await session.scalar(
                select(Catalog).where(
                    Catalog.organization_id == org_id,
                    Catalog.slug == DEFAULT_CATALOG_SLUG,
                )
            )
            if catalog:
                return str(catalog.id)

            store = await session.scalar(
                select(MerchantStore).where(
                    MerchantStore.organization_id == org_id,
                    MerchantStore.slug == DEFAULT_STORE_SLUG,
                )
            )
            if not store:
                store = MerchantStore(
                    organization_id=org_id,
                    name="Default Store",
                    slug=DEFAULT_STORE_SLUG,
                )
                session.add(store)
                await session.flush()

            catalog = Catalog(
                organization_id=org_id,
                store_id=store.id,
                name="Default Products",
                slug=DEFAULT_CATALOG_SLUG,
                resource_type="product",
            )
            session.add(catalog)
            await session.flush()
            await session.commit()
            return str(catalog.id)

    async def upsert_products(
        self,
        organization_id: str,
        catalog_id: str,
        products: Iterable[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        org_id = UUID(str(organization_id))
        catalog_uuid = UUID(str(catalog_id))
        persisted: List[Dict[str, Any]] = []

        async with self.db.async_session() as session:
            catalog = await session.scalar(
                select(Catalog).where(Catalog.id == catalog_uuid, Catalog.organization_id == org_id)
            )
            if not catalog:
                raise ValueError("Catalog does not belong to organization")

            for product in products:
                external_id = str(product["id"])
                item = await session.scalar(
                    select(CatalogItem).where(
                        CatalogItem.organization_id == org_id,
                        CatalogItem.catalog_id == catalog_uuid,
                        CatalogItem.external_id == external_id,
                    )
                )
                if item:
                    item.title = product["title"]
                    item.description = product.get("description")
                    item.url = product.get("url")
                    item.brand = product.get("brand")
                    item.category = product.get("category")
                    item.sub_category = product.get("sub_category")
                    item.document = product
                    item.status = "active"
                    item.deleted_at = None
                    item.index_version += 1
                    item.index_status = "pending"
                    item.index_error = None
                else:
                    item = CatalogItem(
                        organization_id=org_id,
                        catalog_id=catalog_uuid,
                        external_id=external_id,
                        resource_type="product",
                        title=product["title"],
                        description=product.get("description"),
                        url=product.get("url"),
                        brand=product.get("brand"),
                        category=product.get("category"),
                        sub_category=product.get("sub_category"),
                        document=product,
                        source_system="import",
                    )
                    session.add(item)
                await session.flush()

                event = CatalogIndexEvent(
                    organization_id=org_id,
                    catalog_id=catalog_uuid,
                    catalog_item_id=item.id,
                    item_version=item.index_version,
                    operation="upsert",
                    payload={"external_id": external_id},
                )
                session.add(event)
                await session.flush()
                persisted.append({
                    **product,
                    "catalog_item_id": str(item.id),
                    "index_event_id": str(event.id),
                })
            await session.commit()
        return persisted

    async def delete_product(self, organization_id: str, external_id: str) -> bool:
        """Soft-delete canonical product and enqueue idempotent derived-index deletion."""
        org_id = UUID(str(organization_id))
        catalog_id = UUID(await self.ensure_default_product_catalog(organization_id))
        async with self.db.async_session() as session:
            item = await session.scalar(
                select(CatalogItem).where(
                    CatalogItem.organization_id == org_id,
                    CatalogItem.catalog_id == catalog_id,
                    CatalogItem.external_id == str(external_id),
                    CatalogItem.resource_type == "product",
                )
            )
            if not item or item.deleted_at:
                return False

            item.status = "deleted"
            item.deleted_at = datetime.now(timezone.utc)
            item.index_version += 1
            item.index_status = "pending"
            item.index_error = None
            session.add(
                CatalogIndexEvent(
                    organization_id=org_id,
                    catalog_id=catalog_id,
                    catalog_item_id=item.id,
                    item_version=item.index_version,
                    operation="delete",
                    payload={"external_id": str(external_id)},
                )
            )
            await session.commit()
            return True

    async def record_index_results(self, outcomes: Iterable[Dict[str, Any]]) -> None:
        event_ids = [UUID(str(outcome["event_id"])) for outcome in outcomes]
        if not event_ids:
            return
        outcome_by_id = {str(outcome["event_id"]): outcome for outcome in outcomes}

        async with self.db.async_session() as session:
            events = (await session.scalars(select(CatalogIndexEvent).where(CatalogIndexEvent.id.in_(event_ids)))).all()
            now = datetime.now(timezone.utc)
            for event in events:
                outcome = outcome_by_id[str(event.id)]
                succeeded = bool(outcome.get("success"))
                if event.status != "processing":
                    event.attempts += 1
                if succeeded:
                    event.status = "indexed"
                    event.available_at = now
                elif event.attempts >= self.max_index_attempts:
                    event.status = "dead"
                    event.available_at = now
                else:
                    event.status = "failed"
                    # Capped exponential backoff: 1s, 2s, 4s ... 5m.
                    event.available_at = now + timedelta(
                        seconds=min(300, 2 ** max(0, event.attempts - 1))
                    )
                event.error = None if succeeded else str(outcome.get("error") or "Indexing failed")
                event.processed_at = now

                item = await session.get(CatalogItem, event.catalog_item_id)
                if item and item.index_version == event.item_version:
                    item.index_status = event.status
                    item.index_error = event.error
                    item.indexed_at = now if succeeded else None
            await session.commit()

    async def claim_index_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Claim retryable events. Row locks prevent duplicate workers processing one event."""
        async with self.db.async_session() as session:
            result = await session.execute(
                select(CatalogIndexEvent, CatalogItem)
                .join(
                    CatalogItem,
                    and_(
                        CatalogItem.id == CatalogIndexEvent.catalog_item_id,
                        CatalogItem.catalog_id == CatalogIndexEvent.catalog_id,
                        CatalogItem.organization_id == CatalogIndexEvent.organization_id,
                    ),
                )
                .where(
                    or_(
                        and_(
                            CatalogIndexEvent.status.in_(["pending", "failed"]),
                            CatalogIndexEvent.available_at <= datetime.now(timezone.utc),
                        ),
                        and_(
                            CatalogIndexEvent.status == "processing",
                            CatalogIndexEvent.available_at <= datetime.now(timezone.utc),
                        ),
                    )
                )
                .order_by(CatalogIndexEvent.created_at)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
            claimed = []
            for event, item in result.all():
                event.status = "processing"
                event.attempts += 1
                event.available_at = datetime.now(timezone.utc) + timedelta(
                    seconds=self.processing_lease_seconds
                )
                claimed.append(
                    {
                        "event_id": str(event.id),
                        "organization_id": str(event.organization_id),
                        "operation": event.operation,
                        "document": item.document,
                        "external_id": str(item.external_id),
                        "payload": event.payload,
                    }
                )
            await session.commit()
        return claimed

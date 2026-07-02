"""
Sync Triggers
SQLAlchemy after_insert / after_update event listeners on the Product model.
Fires SyncPipeline.sync_product() asynchronously so the DB commit is not blocked.
"""
import asyncio
from typing import Any

from sqlalchemy import event

from app.infrastructure.db.models import Product
from app.utils.logger import get_logger

logger = get_logger("sync_triggers")

# Module-level reference to the pipeline; set by register_triggers()
_pipeline = None


def _product_orm_to_dict(product: Product) -> dict:
    """Convert a Product ORM instance to the dict shape SyncPipeline expects."""
    return {
        "id": product.id,
        "name": product.name,
        "title": product.title,
        "brand": product.brand,
        "category": product.category,
        "sub_category": product.sub_category,
        "description": product.description,
        "url": product.url,
        "price": product.price,
        "tags": product.tags,
        "images": product.images,
        "availability": product.availability,
        "rating": product.rating,
        "stock": product.stock,
        "online_available": product.online_available,
        "metadata": product.extra_data,
    }


def _fire_sync(product: Product) -> None:
    """Schedule a sync in the running event loop (non-blocking)."""
    if _pipeline is None:
        return

    product_dict = _product_orm_to_dict(product)

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(_pipeline.sync_product(product_dict))
        else:
            loop.run_until_complete(_pipeline.sync_product(product_dict))
    except Exception as e:
        logger.error(f"Failed to schedule sync for product {product.id}: {e}")


def register_triggers(pipeline: Any) -> None:
    """
    Register SQLAlchemy ORM event listeners.
    Call this once after the pipeline is ready (e.g. in PostgresClient.connect()).
    """
    global _pipeline
    _pipeline = pipeline

    @event.listens_for(Product, "after_insert")
    def _on_insert(mapper, connection, target: Product):
        logger.debug(f"after_insert fired for product {target.id}")
        _fire_sync(target)

    @event.listens_for(Product, "after_update")
    def _on_update(mapper, connection, target: Product):
        logger.debug(f"after_update fired for product {target.id}")
        _fire_sync(target)

    logger.info("✅ Sync triggers registered on Product model")

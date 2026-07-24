# Canonical Catalog Foundation

## Purpose

Introduce PostgreSQL structures that can become Mercury's canonical, tenant-owned catalog for products, documents, assets, and content. This is the prerequisite for secure product APIs, durable indexing, and tenant-safe caches.

## Constraints

- PostgreSQL is the canonical v1 catalog.
- Existing `products` data and endpoints remain available during migration.
- A tenant can own multiple merchant stores, sellers, and catalogs.
- Marketplace support needs seller isolation in the schema now, even if the first UI exposes one store and one catalog.
- Resource-specific APIs share infrastructure but retain resource-specific schemas and ranking profiles.

## Chosen approach

Create additive catalog tables rather than changing `products.id` into a composite key in place. The legacy product model uses a global string primary key, which cannot safely represent equal external IDs in multiple tenants. Replacing that key would be a high-risk breaking migration.

```text
Organization (tenant, region)
  ├── MerchantStore
  ├── Seller
  └── Catalog
        └── CatalogItem
              └── optional parent CatalogItem (variant)
```

`CatalogItem` is the canonical generic record. It stores a UUID identity, a source-specific external ID, a resource type, normalized retrieval fields, source metadata, and an extensible JSON document. Products will use `resource_type = product`; documents, content, and assets will reuse the same ownership and lifecycle model.

## Ownership and constraints

- `merchant_stores`, `sellers`, and `catalogs` belong to an organization.
- `catalogs` may reference a store and seller, both constrained to the same organization.
- `catalog_items` carry both `organization_id` and `catalog_id`; a composite foreign key enforces that the catalog belongs to that organization.
- `(organization_id, catalog_id, external_id)` is unique, allowing the same source ID in distinct tenant catalogs.
- Item status and soft deletion prevent deleted records from being returned or indexed.
- Organization gains a validated deployment-region field with `us-east-1` as the initial default.

## Migration strategy

1. Add the new structures and indexes.
2. Create a default merchant store/catalog per existing organization in a follow-up migration or explicit backfill command.
3. Change import/sync paths to upsert `CatalogItem` records before emitting index work.
4. Add tenant-aware product read APIs backed by catalog items.
5. Retire the legacy global product path only after compatibility endpoints and data migration are complete.

## Non-goals for this slice

- Migrating existing product rows.
- Changing public product API response shapes.
- Running an async indexing worker.
- Implementing connector synchronization.
- Replacing Typesense schemas.

## Testing

Metadata tests will assert the ownership columns, unique constraints, and indexes. Migration review will verify explicit foreign keys and a reversible downgrade. Runtime catalog-import tests are deferred until the repository layer and importer migration slice.

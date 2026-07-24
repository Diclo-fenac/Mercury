# Canonical Catalog Write and Index Outbox

## Purpose

Move catalog ingestion toward the agreed PostgreSQL-first model. A catalog write must persist a canonical record and a pending search-index event atomically before Typesense is called.

## Design

```text
Importer/API
  → CatalogService
  → PostgreSQL transaction
       ├── CatalogItem upsert (index_status=pending, index_version++)
       └── CatalogIndexEvent (pending)
  → Typesense adapter
  → mark matching events/items indexed or failed
```

`CatalogIndexEvent` is the durable retry boundary. The initial slice indexes synchronously for compatibility, but any Typesense failure remains recorded in PostgreSQL rather than losing catalog state. A later worker will claim and replay pending events.

## Scope

- Add item index-state fields and an index-outbox table.
- Provision a default store/catalog per organization on first canonical write.
- Upsert normalized product records into `catalog_items` before Typesense.
- Record per-document Typesense outcomes and mark durable index state.
- Preserve current import endpoint shapes and tenant Typesense collection names.

## Non-goals

- Background worker/retry scheduler.
- Migrating individual admin product upsert/delete endpoints.
- Changing product read APIs to catalog items.
- Deleting legacy product data.

## Failure behavior

- PostgreSQL failure: no Typesense call; importer reports failure.
- Embedding failure: canonical records remain pending; importer reports failure.
- Typesense failure: canonical records and events remain retryable with a recorded error.
- Redis failure is irrelevant to catalog persistence.

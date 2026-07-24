# Canonical Catalog Write and Index Outbox Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist catalog products in PostgreSQL and record durable index events before synchronously indexing Typesense.

**Architecture:** A catalog repository owns default catalog provisioning and transactional item/outbox writes. The importer orchestrates normalization, embeddings, Typesense writes, and durable result state; it never treats Typesense as authoritative.

**Tech Stack:** Python, SQLAlchemy/PostgreSQL, Alembic, Typesense, pytest.

---

### Task 1: Add index state and outbox schema

**Files:**
- Modify: `app/domain/tenants/models.py`
- Create: `alembic/versions/<revision>_catalog_index_outbox.py`
- Modify: `tests/unit/test_catalog_models.py`

- [ ] Write failing metadata tests.
- [ ] Add model and reversible migration.
- [ ] Run metadata and offline Alembic validation.

### Task 2: Add catalog repository and service

**Files:**
- Create: `app/infrastructure/catalog/repository.py`
- Create: `app/domain/catalogs/service.py`
- Create: `tests/unit/test_catalog_service.py`

- [ ] Write fake-session tests for normalized writes and default-catalog resolution.
- [ ] Implement transactional upsert/outbox behavior.
- [ ] Run focused tests.

### Task 3: Migrate importer persistence order

**Files:**
- Modify: `app/domain/tenants/importer.py`
- Modify: `app/container.py`
- Modify: `app/infrastructure/search/typesense.py`
- Create: `tests/unit/test_catalog_importer.py`

- [ ] Write failing importer flow tests.
- [ ] Persist before indexing; record partial index outcomes.
- [ ] Run focused tests and static checks.

# Canonical Catalog Foundation Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add tenant-owned catalog schema primitives that support canonical product and generic-document records without breaking legacy product APIs.

**Architecture:** Add additive SQLAlchemy models and an Alembic migration for merchant stores, sellers, catalogs, and catalog items. Preserve the legacy `products` table until import and read paths are migrated in later slices.

**Tech Stack:** Python 3.10+, SQLAlchemy 2.x, Alembic, PostgreSQL UUID/JSONB, pytest.

---

## Chunk 1: Domain schema

### Task 1: Add tenant catalog models

**Files:**
- Modify: `app/domain/tenants/models.py`
- Create: `tests/unit/test_catalog_models.py`

- [ ] **Step 1: Write metadata tests for region, ownership, catalog-item uniqueness, parent variants, and tenant/catalog indexes.**
- [ ] **Step 2: Run `pytest tests/unit/test_catalog_models.py -q`; expect failure because the models do not exist.**
- [ ] **Step 3: Add `MerchantStore`, `Seller`, `Catalog`, and `CatalogItem` models with explicit ownership and lifecycle columns.**
- [ ] **Step 4: Re-run focused test; expect pass.**

## Chunk 2: Migration

### Task 2: Add reversible PostgreSQL migration

**Files:**
- Create: `alembic/versions/<revision>_canonical_catalog_foundation.py`
- Modify: `tests/unit/test_catalog_models.py`

- [ ] **Step 1: Add assertions covering migration revision linkage and required tables/index names.**
- [ ] **Step 2: Create the migration with composite catalog-item ownership constraints and downgrade in dependency-safe order.**
- [ ] **Step 3: Re-run focused metadata tests; expect pass.**

## Chunk 3: Verification

### Task 3: Validate schema code and document migration order

**Files:**
- Modify: `docs/RUNBOOK.md`

- [ ] **Step 1: Run focused tests.**
- [ ] **Step 2: Run `ruff check app tests` and `python -m compileall -q app tests`.**
- [ ] **Step 3: Add migration/backfill notes to the runbook; do not claim legacy products are migrated.**

## Execution notes

- Do not alter `products.id` in this slice.
- Use UUID primary keys internally and source-specific `external_id` for connector upserts.
- Preserve API compatibility while the catalog importer is migrated in the next slice.
- Do not create a default catalog implicitly inside the migration; creation/backfill needs explicit operational control.

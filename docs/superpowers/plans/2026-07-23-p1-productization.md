# P1 Productization Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn P0-safe search into a managed product: read-only MCP, provider-neutral AI, merchant controls, reliable connectors, and observable operations.

**Architecture:** PostgreSQL remains canonical. Typesense stays derived. Every REST route, MCP tool, cache key, worker job, and audit event receives tenant context first. MCP routes into existing orchestrators; it never becomes another search stack.

**Tech Stack:** FastAPI, PostgreSQL/Alembic, Redis, Typesense, Python MCP SDK, OIDC, Prometheus.

---

## Task 1: Regional read-only MCP

**Objective:** Regional streamable-HTTP MCP: search/get/autocomplete/similar/recommend/chat/collections/categories. No writes.

**Files:** Create `app/mcp/server.py`, `app/mcp/auth.py`, `app/mcp/tools/catalog.py`, `tests/unit/test_mcp_tools.py`. Modify `requirements.txt`, `app/settings.py`, `app/container.py`, `main.py`, `docs/RUNBOOK.md`.

**Dependencies:** P0 tenant resolver, catalog/search/recommendation/chat orchestrators.

**Risks:** Tenant/filter bypass; write-tool exposure; unbounded result size.

**Acceptance:** API-key + OIDC service-account auth; schema/limit/scope/audit for each tool; shared conversation storage uses `channel=mcp`; regional endpoint only; no catalog/admin write tool.

**Complexity / impact:** High / high.

- [ ] Write denied-scope, wrong-tenant, unknown-tool, oversized-query tests.
- [ ] Add MCP transport, auth adapter, read-only registry.
- [ ] Route every tool through current orchestrators.
- [ ] Add tool metrics, runbook, contract tests.
- [ ] Run focused test, full suite, compatibility smoke test; commit.

## Task 2: Identity, API scopes, service accounts, audit

**Objective:** Tenant-local RBAC, scoped API keys, OIDC JWKS verification, service accounts, immutable audit records.

**Files:** Create `app/domain/identity/`, `app/infrastructure/identity/oidc.py`, migration, `tests/unit/test_identity_scope.py`. Modify `app/api/dependencies.py`, tenant models, admin endpoints, settings.

**Dependencies:** Task 1; existing tenant model.

**Risks:** Key/JWT compatibility break; accepting wrong issuer/audience; privilege escalation.

**Acceptance:** Hash-only key storage; exact route/tool scopes; issuer/audience/expiry/JWKS validation; audit tenant/actor/action/target/request/outcome; documented key deprecation path.

**Complexity / impact:** High / high.

- [ ] Write expiry, revocation, wrong-audience, scope, cross-tenant, audit tests.
- [ ] Add migration/service and compatibility adapter.
- [ ] Enforce all entry paths: REST, WebSocket, worker, MCP.
- [ ] Write rotation/OIDC/audit runbooks; test migration; commit.

## Task 3: Idempotent source connectors

**Objective:** CSV, Shopify, WooCommerce, Magento, REST import, webhook sync into canonical catalog/outbox.

**Files:** Create `app/domain/connectors/`, `app/infrastructure/connectors/`, connector migration, `app/api/v1/endpoints/connectors.py`, `tests/integration/test_connector_sync.py`. Modify catalog service/repository/container/runbook.

**Dependencies:** P0 catalog outbox; Task 2 secret/scopes/audit.

**Risks:** Duplicate/out-of-order webhooks; source throttling; destructive full-sync; secrets in logs.

**Acceptance:** Idempotency key, cursor/checkpoint, signed webhook validation, encrypted credentials, dry run, source status, DLQ/retry visibility. Canonical record always precedes index event.

**Complexity / impact:** High / high.

- [ ] Write duplicate, cursor resume, invalid signature, source delete tests.
- [ ] Build shared source-normalization contract.
- [ ] Deliver CSV first; one connector per commit afterwards.
- [ ] Add status/recovery APIs and runbook; run service-backed tests.

## Task 4: Merchant rules and experiments

**Objective:** Versioned synonyms, redirects, boosts, buries, pins, collections, ranking profiles, deterministic experiments.

**Files:** Create `app/domain/merchandising/`, migration, `app/api/v1/endpoints/merchandising.py`, `tests/unit/test_merchandising.py`. Modify search orchestrator, tenant service, cache keys.

**Dependencies:** P0 search explainability/cache revision; Task 2 admin scopes/audit.

**Risks:** Rules hide relevant products; experiment cache cross-over; stale config.

**Acceptance:** Ordered rule evaluation after retrieval and before personalization/pagination; preview/version/rollback; stable assignment; ranking breakdown names rule/experiment; config bumps only tenant-local search cache revision.

**Complexity / impact:** High / high.

- [ ] Write conflicting-rule, pinned-pagination, preview, rollback, variant-cache tests.
- [ ] Implement immutable rule versions/evaluator.
- [ ] Add admin CRUD/preview/rollback with audit.
- [ ] Add rule and experiment metrics; relevance fixtures; commit.

## Task 5: AI provider abstraction and budgets

**Objective:** OpenAI hosted default; Anthropic/Gemini/Ollama/OpenRouter/BYOK adapters; provider fallback, streaming, budgets, prompt experiments.

**Files:** Create `app/intelligence/providers/`, `app/domain/ai_budget/`, migration, `tests/unit/test_ai_provider_routing.py`. Modify engine, container, settings, chat endpoints, runbook.

**Dependencies:** P0 grounded-answer/citation contract; Tasks 2 and 4.

**Risks:** Provider output bypasses citations; cost runaway; BYOK secret leak; fallback changes answer semantics.

**Acceptance:** Shared generate/stream/embed capabilities; every catalog answer remains grounded/cited; per-tenant hard/soft budgets; model/provider/token/cost telemetry excludes prompt/secrets; fallback deterministic.

**Complexity / impact:** High / high.

- [ ] Write provider contract/budget/fallback/grounding tests.
- [ ] Extract current provider behind interface; add OpenAI first.
- [ ] Add budget enforcement, prompt version assignment, telemetry.
- [ ] Run provider contract suite/full suite; commit.

## Task 6: Dedicated workers and operational policy

**Objective:** Move index replay out of API process. Add DLQ controls, Redis policy, alerts, restore drill.

**Files:** Create `app/workers/catalog_index.py`, observability modules, worker Compose service, `tests/integration/test_outbox_replay.py`. Modify main, Compose files, Redis client, runbook.

**Dependencies:** P0 outbox/metrics.

**Risks:** Duplicate workers; lease loss; Redis outage weakens abuse protection; bad migration rollout.

**Acceptance:** Production API replicas do not replay indexes; lease/idempotency/DLQ works; dashboard covers queue age/retries/cache hit/Redis eviction/latency; endpoint-specific Redis fail policy documented; backup restore drill passes.

**Complexity / impact:** Medium / high.

- [ ] Write lease expiry, replay, DLQ, duplicate worker, Redis outage tests.
- [ ] Add worker entrypoint/Compose role.
- [ ] Add metrics, alerts, cache policy, restore docs.
- [ ] Run Compose config, migration smoke, worker integration test; commit.

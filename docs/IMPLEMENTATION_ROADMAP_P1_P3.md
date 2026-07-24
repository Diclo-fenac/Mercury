# Mercury P1-P3 Implementation Plan

> **For agentic workers:** REQUIRED: Read this document, the repository documentation, and the P0 implementation before changing code. Use the repository's planning workflow for each task. Do not implement P1, P2, or P3 work until the user explicitly approves the target phase.

**Goal:** Extend Mercury from a tenant-safe P0 foundation into a production-ready AI-native search, merchandising, analytics, integration, and enterprise platform.

**Architecture:** Keep PostgreSQL as the canonical source for catalog and customer data. Keep Typesense behind the search boundary, Redis behind the cache boundary, and AI providers behind a common provider interface. Every request, cache entry, background job, search document, image object, analytics event, and MCP tool must carry explicit tenant scope.

**Tech Stack:** FastAPI, Python, PostgreSQL, SQLAlchemy, Alembic, Redis, Typesense, local embeddings, provider-based LLMs, MinIO/local storage, Prometheus, Grafana, Docker Compose, pytest, Ruff.

---

## 0. Operating Contract for the Next Model

### 0.1 Current state

P0 is implemented. It includes:

- Canonical PostgreSQL catalog.
- Durable catalog index outbox and retry worker.
- Tenant-scoped product, user, conversation, memory, image, cache, and WebSocket paths.
- Typesense keyword/vector retrieval with weighted RRF.
- PostgreSQL rehydration after search retrieval.
- Grounded AI responses with product citations.
- Migration-owned database schema.
- Redis cache-key hardening and rate limiting.
- Test-mode isolation from external services.

Latest local baseline:

```text
ruff check app tests alembic main.py       PASS
python -m compileall -q app main.py        PASS
pytest -q                                  72 passed, 29 skipped
docker compose config -q                   PASS
docker compose -f docker-compose.prod.yml config -q  PASS
alembic heads                              9c13d4e6f2a7
```

The skipped tests are external-service integration suites. Do not describe them as production verification until PostgreSQL, Redis, Typesense, and storage are running and the integration suite passes.

### 0.2 Behavior rules

- Plan before implementation.
- Inspect existing code and docs before changing a subsystem.
- Work one task at a time.
- Write a failing or boundary test before implementation when practical.
- Preserve public API compatibility within the current major version.
- Add migrations for schema changes; never rely on `create_all` in production.
- Never allow a caller-supplied tenant, user, seller, collection, or conversation ID to override authenticated scope.
- Never cache tenant data under a global key.
- Never allow an LLM to invent catalog facts or execute unapproved write tools.
- Update documentation and OpenAPI when behavior changes.
- Run focused tests after each task and the full suite at phase completion.
- Stop and report if a requirement conflicts with tenant isolation, data safety, or an approved architecture decision.

### 0.3 Communication rules

- Do not send repeated progress messages.
- Send one short start message when work begins.
- Send an immediate blocker message if external authority or a user decision is required.
- End each task with changed files, verification, risks, and remaining work.
- Do not claim a phase complete while required tests are skipped or failing.

### 0.4 Required review order

For every task:

1. Read relevant documentation and current implementation.
2. Write or update tests.
3. Implement the smallest complete change.
4. Run focused lint and tests.
5. Review tenant isolation, cache keys, failure behavior, and backwards compatibility.
6. Update docs/OpenAPI.
7. Run the phase regression suite.
8. Ask for approval before beginning the next phase.

---

## 1. Shared Design Rules

### 1.1 Tenant context

Use `TenantContext` from `app/api/dependencies.py` as the request boundary. Tenant scope must be available to:

- REST endpoints.
- MCP requests.
- WebSocket connections.
- Search orchestration.
- AI tool execution.
- Background catalog jobs.
- Redis cache keys.
- Typesense collection resolution.
- Analytics and usage events.
- Image metadata and object paths.

### 1.2 Canonical data flow

```text
External source -> Import/sync pipeline -> PostgreSQL canonical catalog
                                      -> Catalog index outbox
                                      -> Typesense derived index
                                      -> Embeddings and AI evidence
```

Typesense is never the source of truth. AI must use canonical, tenant-filtered catalog evidence.

### 1.3 Search boundary

Public resource namespaces may differ:

```text
/api/v1/products/search
/api/v1/documents/search
/api/v1/assets/search
/api/v1/content/search
```

Internally, use shared parser, retrieval, ranking, filtering, facets, explainability, and caching interfaces. Resource-specific schemas and ranking profiles stay explicit.

### 1.4 Backwards compatibility

- Public REST APIs: 12-month deprecation window.
- SDKs: 6-month deprecation window.
- Experimental APIs: compatibility not guaranteed.
- Breaking changes require a major version and migration guide.
- Existing response fields must remain stable unless explicitly deprecated.

---

# P1 — High Priority

## P1 outcome

Merchants can control search, developers can integrate through MCP and stable APIs, AI providers are replaceable, and the widget is safe for production storefront use.

## P1 dependency order

```text
P1.1 MCP foundation
       |
P1.2 AI provider abstraction ---- P1.3 Search controls
       |                              |
       +------------------------------+
                         |
                  P1.4 Redis hardening
                         |
                  P1.5 Widget readiness
```

P1.1 and P1.2 may be developed in parallel. P1.3 depends on the existing search pipeline. P1.4 must run before high-QPS production rollout. P1.5 consumes the stable API and search behavior.

## P1.1 — Read-only MCP server

### Objective

Expose Mercury search and shopping capabilities through a tenant-safe MCP server. V1 must remain read-only.

### Approved v1 tools

- `search_products`
- `search_documents`
- `get_product`
- `autocomplete`
- `find_similar_products`
- `recommend_products`
- `chat_catalog`
- `get_collections`
- `get_categories`

### Explicitly excluded

- Product creation or deletion.
- Price or inventory mutation.
- Bulk imports.
- Ranking-rule mutation.
- AI-setting mutation.
- Merchant administration.

### Files to inspect or create

- Create: `app/mcp/server.py` — MCP server entrypoint and transport wiring.
- Create: `app/mcp/auth.py` — API-key and OIDC service-account authentication.
- Create: `app/mcp/context.py` — tenant and user context construction.
- Create: `app/mcp/schemas.py` — strict tool input/output schemas.
- Create: `app/mcp/tools/search.py` — search/autocomplete tools.
- Create: `app/mcp/tools/catalog.py` — product/category/collection read tools.
- Create: `app/mcp/tools/recommendations.py` — recommendation tools.
- Create: `app/mcp/tools/chat.py` — grounded catalog chat tool.
- Modify: `app/container.py` — register MCP-facing service dependencies only if needed.
- Modify: `app/api/dependencies.py` — reuse authentication primitives; do not duplicate JWT validation.
- Modify: `app/settings.py` — MCP enablement, regional endpoint, issuer, audience, and token settings.
- Modify: `main.py` — mount MCP transport or launch a dedicated MCP app according to chosen deployment mode.
- Create: `tests/unit/test_mcp_auth.py`.
- Create: `tests/unit/test_mcp_tools.py`.
- Create: `tests/integration/test_mcp_tenant_isolation.py`.
- Modify: `docs/RUNBOOK.md` — deployment and credential operations.
- Create: `docs/MCP.md` — client setup, tools, scopes, errors, and examples.

### Dependencies

- Existing `TenantContext` and API-key resolution.
- Existing `SearchOrchestrator`, `ProductService`, recommendation services, and `ChatOrchestrator`.
- Grounded AI implementation from P0.
- MCP SDK/version chosen after checking project dependency policy.

### Required behavior

- Every tool resolves tenant from credential, never tool input.
- API keys work for development and normal hosted clients.
- OIDC service accounts use issuer, audience, signature, expiry, and scope validation.
- Tool input has hard size and limit bounds.
- Unknown tool names fail safely.
- Catalog chat returns product citations.
- No write tool is registered in v1.
- MCP and REST conversations share the existing conversation model where a user identity exists.
- Regional endpoints are tenant-scoped behind one shared service; dedicated enterprise endpoints remain future work.

### Acceptance criteria

- Valid API-key request returns tenant-local results.
- Same product ID queried with another tenant credential returns not found or no result.
- Missing, expired, malformed, or wrong-audience OIDC token fails.
- Tool cannot request another Typesense collection.
- Tool cannot write catalog or configuration data.
- MCP schema tests and tenant-isolation integration tests pass.
- Documentation includes curl/client examples and error contracts.

### Risks

- MCP SDK transport changes.
- Authentication duplication causing inconsistent policy.
- LLM clients attempting unbounded tool inputs.
- Conversation identity mismatch between MCP and REST.

### Complexity / impact

Medium-high complexity. High developer-integration impact; high security impact.

## P1.2 — AI provider and embedding abstraction

### Objective

Make AI and embedding providers replaceable without changing orchestration, grounding, citations, or merchant controls.

### Supported providers

- OpenAI — hosted default.
- Anthropic.
- Google Gemini.
- Ollama.
- OpenRouter.
- Local embedding provider.
- OpenAI, Gemini, Voyage AI, and tenant BYO embeddings.

### Files to inspect or create

- Create: `app/intelligence/providers/base.py` — common chat, streaming, tool, and token-usage interfaces.
- Create: `app/intelligence/providers/openai.py`.
- Create: `app/intelligence/providers/anthropic.py`.
- Create: `app/intelligence/providers/gemini.py`.
- Create: `app/intelligence/providers/ollama.py`.
- Create: `app/intelligence/providers/openrouter.py`.
- Create: `app/intelligence/providers/factory.py` — validated provider selection.
- Create: `app/addons/embeddings/providers/base.py`.
- Create: provider-specific embedding adapters under `app/addons/embeddings/providers/`.
- Modify: `app/intelligence/engine.py` — use provider interface while preserving grounding guardrails.
- Modify: `app/container.py` — provider registration and lifecycle.
- Modify: `app/settings.py` — provider configuration and BYOK policy.
- Modify: `app/models/responses.py` — provider/cost metadata only where public API requires it.
- Create: `tests/unit/test_ai_provider_contract.py`.
- Create: `tests/unit/test_ai_grounding_across_providers.py`.
- Create: `tests/unit/test_embedding_provider_contract.py`.
- Create: `docs/AI_PROVIDERS.md`.

### Required behavior

- Provider interface supports normal completion, streaming, tool calls, timeout, cancellation, usage, and provider errors.
- Orchestrator remains provider-agnostic.
- Catalog evidence is injected consistently for every provider.
- Provider output is rejected if it cites unknown product IDs.
- Provider timeouts use deterministic catalog fallback.
- BYOK credentials are never logged or cached in plaintext.
- Merchant AI budget is checked before paid calls.
- Usage event records provider, model, input tokens, output tokens, estimated cost, tenant, and request ID.

### Acceptance criteria

- Switching provider requires configuration, not orchestration changes.
- Mock contract suite passes for every adapter.
- No provider can bypass tenant search tools.
- Cost limit prevents a request that exceeds merchant budget.
- Streaming begins within the configured target when provider supports streaming.

### Risks

- Provider tool-call semantics differ.
- Provider output formats and streaming events differ.
- Cost estimation may be inaccurate without current provider pricing.
- BYOK secret rotation and self-hosted secret storage.

### Complexity / impact

High complexity. High platform flexibility and cost-control impact.

## P1.3 — Search quality and merchant controls

### Objective

Give merchants deterministic, explainable control over search ranking and query behavior.

### Features

- Synonyms.
- Query redirects.
- Pinned products.
- Boost and bury rules.
- Facet configuration.
- Search filters.
- Collections.
- Merchandising campaigns.
- Ranking profiles.
- Ranking, synonym, and AI-prompt experiments.
- Zero-result recovery.
- Search explanation.

### Files to inspect or modify

- Modify: `app/addons/search/hybrid.py` — retrieval inputs and explainable ranking evidence.
- Modify: `app/orchestrators/search_orchestrator.py` — rule evaluation order and experiment assignment.
- Modify: `app/infrastructure/search/typesense.py` — synonym, collection, facet, and ranking adapter operations.
- Modify: `app/domain/tenants/models.py` — rules, campaigns, experiments, and ranking profiles.
- Modify: `app/domain/tenants/service.py` — tenant-scoped rule CRUD and cache invalidation.
- Modify: `app/api/v1/endpoints/admin.py` — merchant management endpoints.
- Modify: `app/api/v1/endpoints/products.py` and `app/api/v1/endpoints/search.py` — stable public search response fields.
- Create: Alembic migration under `alembic/versions/` for rule and experiment tables.
- Create: `app/domain/search/rules.py` — validated rule evaluation.
- Create: `app/domain/search/experiments.py` — deterministic assignment and exposure events.
- Create: `tests/unit/test_search_rule_order.py`.
- Create: `tests/unit/test_search_experiments.py`.
- Create: `tests/unit/test_zero_result_recovery.py`.
- Create: `tests/integration/test_merchant_rules_isolation.py`.
- Update: `docs/API.md` or the repository's current API reference location.

### Required rule order

```text
Request validation
-> tenant configuration
-> query normalization
-> redirects
-> retrieval
-> hard filters
-> bury rules
-> boosts
-> personalization if enabled
-> pins
-> pagination
-> explanation
```

Hard filters must never be overridden by boosts or pins. Every applied rule must be visible in merchant-facing explanation data.

### Acceptance criteria

- Same query produces deterministic results when experiments are disabled.
- Rule precedence is tested and documented.
- Pinned products cannot bypass inventory or tenant filters.
- A/B assignment is stable for a user/session and isolated by experiment.
- Merchants can preview rules before activation.
- Cache invalidation occurs after rule changes.

### Complexity / impact

High complexity. Highest direct search-quality and merchant-value impact in P1.

## P1.4 — Redis production hardening

### Objective

Make Redis behavior safe and predictable under tenant traffic, cache misses, invalidation, and partial outages.

### Files to inspect or modify

- Modify: `app/infrastructure/cache/keys.py` — complete opaque key inventory.
- Modify: `app/infrastructure/cache/redis.py` — timeouts, retries, metrics, invalidation, circuit behavior.
- Modify: `app/orchestrators/search_orchestrator.py` — cache fallback and stampede control.
- Modify: `app/domain/search/suggestions_service.py` — tenant-aware suggestion keys.
- Modify: `app/domain/products/trending_service.py` — tenant-aware cache keys and canonical DB calls.
- Modify: `app/addons/personalization/scorer.py` — all session/context keys.
- Modify: `app/domain/recommendations/personalization_service.py` — tenant scope or remove unused legacy path.
- Modify: `app/api/dependencies.py` — distributed rate-limit policy.
- Modify: `app/settings.py` — Redis timeout, retry, and fail-open/fail-closed settings.
- Create: `tests/unit/test_cache_key_inventory.py`.
- Create: `tests/unit/test_cache_failure_behavior.py`.
- Create: `tests/integration/test_redis_tenant_isolation.py`.
- Modify: `docs/RUNBOOK.md` — Redis recovery, memory, eviction, and outage behavior.

### Required behavior

- No tenant-sensitive value under a global cache key.
- No Redis `KEYS` command in request paths.
- Bounded connection and command timeouts.
- Search cache stampede protection for hot keys.
- Explicit policy when Redis is unavailable.
- Rate limiting remains distributed when Redis is healthy.
- Metrics: hit, miss, error, latency, evictions, memory, rate-limit rejects.
- Cache invalidation is tested after product, rule, tenant, and user updates.

### Acceptance criteria

- Key inventory test rejects raw user IDs, API keys, query text, and tenant-sensitive global keys where opaque keys are required.
- Two tenants cannot read each other's cache data.
- Redis outage does not crash catalog search; behavior matches documented fallback policy.
- Rate limits work across two application workers with one Redis instance.
- Hot-key test shows bounded duplicate recomputation.

### Complexity / impact

Medium-high complexity. High reliability and security impact.

## P1.5 — Widget production readiness

### Objective

Make the embeddable storefront widget fast, accessible, responsive, and safe to customize.

### Files to inspect or modify

- Inspect: `widget/` — current build, runtime, API client, and styles.
- Modify: widget search and autocomplete components.
- Modify: widget keyboard and focus handling.
- Modify: widget loading/error/empty states.
- Modify: widget theme and CSS isolation.
- Modify: `app/api/v1/endpoints/widget.py` — stable widget API and configuration validation.
- Create or modify: `tests/e2e/` — Playwright widget flows.
- Create: widget accessibility tests using axe or equivalent.
- Update: `docs/WIDGET.md`.

### Required behavior

- Keyboard navigation works for autocomplete and results.
- Screen readers receive labels, status updates, and result counts.
- No tenant data appears in DOM or network responses outside current tenant.
- Widget works on narrow mobile layouts.
- Search input has debounce and cancellation.
- Loading, empty, error, and offline states are explicit.
- Merchant theme cannot break contrast or layout.
- Bundle size and input-to-result latency have documented budgets.

### Acceptance criteria

- Playwright smoke suite passes on desktop and mobile viewports.
- Accessibility checks pass without critical violations.
- Performance budget is measured in CI.
- Widget installation docs work from a clean HTML page.

### Complexity / impact

Medium complexity. High merchant conversion and developer-experience impact.

## P1 phase gate

Before calling P1 complete:

- MCP tools pass authentication and tenant-isolation tests.
- AI provider contract tests pass.
- Search rules have deterministic precedence tests.
- Redis failure and isolation tests pass.
- Widget E2E/accessibility/performance tests pass.
- `ruff`, compile, unit, integration, and relevant E2E checks pass.
- OpenAPI and docs are updated.
- User approves P2 start.

---

# P2 — Medium Priority

## P2 outcome

Mercury becomes measurably smarter, supports major catalog sources, and scales beyond the initial single-merchant deployment model.

## P2.1 — Opt-in personalization

### Objective

Improve relevance for consenting users without making ranking unpredictable, biased, or privacy-invasive.

### Files to inspect or modify

- Modify: `app/addons/personalization/scorer.py`.
- Modify: `app/domain/users/service.py`.
- Modify: `app/infrastructure/db/postgres.py`.
- Modify: tenant customer models and create an Alembic migration for signal storage.
- Modify: `app/api/v1/endpoints/telemetry.py`.
- Modify: `app/orchestrators/search_orchestrator.py`.
- Create: privacy/retention service under `app/domain/privacy/` if no existing boundary exists.
- Create: `tests/unit/test_personalization_cold_start.py`.
- Create: `tests/unit/test_personalization_opt_in.py`.
- Create: `tests/integration/test_personalization_tenant_isolation.py`.
- Update: privacy and data-retention docs.

### Signals

- Clicks.
- Add-to-cart events.
- Purchases.
- Recency.
- Popularity.
- Anonymous session behavior.
- Returning-user behavior.

### Required behavior

- Disabled by default.
- Consent and merchant configuration required.
- Anonymous profiles use short-lived pseudonymous IDs.
- Cold-start falls back to deterministic merchant ranking.
- Personalization has bounded weight and cannot override hard filters.
- Merchants can inspect and disable signals.
- Retention jobs enforce 90-day search-event and configured conversation retention.

### Acceptance criteria

- Disabled personalization yields deterministic results.
- Enabled personalization improves an offline relevance metric without hiding eligible products unfairly.
- User deletion removes or anonymizes retained signals.
- Cross-tenant signal reads fail.

### Complexity / impact

High complexity. High relevance impact; high privacy risk.

## P2.2 — Recommendation engine

### Objective

Deliver reliable similar, complementary, frequently-bought-together, trending, and inventory-aware recommendations.

### Files to inspect or modify

- Modify: `app/domain/recommendations/engine.py`.
- Modify: `app/orchestrators/recommendation_orchestrator.py`.
- Modify: product canonical query methods.
- Modify: recommendation cache keys and invalidation.
- Create: evaluation fixtures and offline metrics under `tests/recommendations/`.
- Update: recommendation API docs.

### Required behavior

- Every recommendation source is tenant-scoped.
- Deleted, hidden, or unavailable products are excluded.
- Explanations identify the strategy used.
- Empty and cold-start cases have deterministic fallback.
- Recommendation cache includes tenant, product, user/session, strategy, and catalog revision.

### Acceptance criteria

- Product detail recommendation endpoints return only canonical tenant products.
- Recommendation strategies have offline precision/recall or hit-rate evaluation.
- Cache invalidates after catalog changes.

### Complexity / impact

Medium-high complexity. Medium-high discovery impact.

## P2.3 — Catalog source integrations

### Objective

Synchronize external catalogs into PostgreSQL without making upstream systems runtime dependencies.

### Integration order

1. CSV.
2. REST API.
3. Webhooks.
4. Shopify.
5. WooCommerce.
6. Magento.

### Files to inspect or create

- Modify: `app/domain/tenants/importer.py`.
- Modify: `app/domain/catalogs/service.py`.
- Modify: `app/infrastructure/catalog/repository.py`.
- Modify: `app/infrastructure/catalog/worker.py`.
- Create: `app/infrastructure/integrations/base.py`.
- Create: integration adapters under `app/infrastructure/integrations/`.
- Create: webhook endpoint module under `app/api/v1/endpoints/`.
- Create: source connection and sync-state models plus Alembic migration.
- Create: `tests/unit/test_import_idempotency.py`.
- Create: `tests/integration/test_catalog_sync_recovery.py`.
- Update: `docs/INTEGRATIONS.md`.

### Required behavior

- External payload maps to canonical catalog schema.
- Idempotency key prevents duplicate imports.
- Upstream outages do not delete valid local data.
- Deletes are explicit and auditable.
- Events enter the durable outbox.
- Retry schedule and dead-letter state are visible.
- Webhooks authenticate signatures and reject replayed events.
- Seller scope is present in schema even for single-merchant MVP.

### Acceptance criteria

- Replaying the same source event produces one canonical version.
- Failed indexing retries without duplicate records.
- Upstream outage leaves the last known-good catalog searchable.
- Sync dashboard/report exposes counts, errors, retries, and dead letters.

### Complexity / impact

High complexity. High customer acquisition and retention impact.

## P2.4 — Semantic image search

### Objective

Replace the current tenant-safe text fallback with actual image-to-product retrieval.

### Files to inspect or create

- Modify: `app/addons/image/processor.py`.
- Modify: `app/orchestrators/image_orchestrator.py`.
- Create: image embedding provider boundary under `app/addons/embeddings/`.
- Modify: `app/infrastructure/search/typesense.py` for image vector fields.
- Modify: catalog index worker to index image embeddings.
- Modify: image storage and metadata retention.
- Create: image-search evaluation tests.
- Update: `docs/IMAGE_SEARCH.md`.

### Providers

- CLIP.
- SigLIP.
- Gemini Vision.
- OpenAI Vision.

### Required behavior

- Images are stored in tenant-partitioned object paths.
- Metadata has explicit owner and tenant.
- Image deletion removes metadata, object, embedding, and cache records.
- Search results rehydrate from canonical PostgreSQL.
- Unsupported image format/size fails before provider cost.
- Provider failure falls back safely.

### Acceptance criteria

- Image query retrieves semantically similar tenant products.
- No cross-tenant image or product result is possible.
- Offline evaluation has top-k relevance targets.
- Image deletion is verifiable across all storage layers.

### Complexity / impact

High complexity. High feature differentiation impact.

## P2.5 — Analytics and merchant reporting

### Objective

Turn search and shopping behavior into trustworthy merchant decisions.

### Files to inspect or create

- Modify: `app/api/v1/endpoints/telemetry.py`.
- Modify: usage/event models and PostgreSQL repository.
- Create: analytics aggregation jobs.
- Create: analytics query service.
- Create: merchant analytics endpoints.
- Create: retention and anonymization jobs.
- Modify: Prometheus metrics only for operational metrics; do not overload Prometheus for warehouse analytics.
- Update: `docs/ANALYTICS.md`.

### Metrics

- Searches.
- Zero-result rate.
- Autocomplete usage.
- CTR.
- Add-to-cart rate.
- Conversion rate.
- Revenue and margin where supplied.
- AI request count/cost.
- Indexing latency and failure rate.

### Acceptance criteria

- All analytics queries require tenant scope.
- Event schema is versioned.
- Duplicate events are idempotently handled.
- Retention policy is enforced automatically.
- Merchant dashboard numbers reconcile with raw event samples.

### Complexity / impact

High complexity. High commercial impact.

## P2.6 — Scale and operations

### Objective

Prove the platform against target traffic and improve operational recovery.

### Files to inspect or create

- Modify: `app/settings.py` and connection configuration.
- Modify: `app/container.py` and worker lifecycle.
- Modify: `app/infrastructure/catalog/worker.py` for dedicated worker mode.
- Modify: `docker-compose.prod.yml`.
- Create: load tests under `tests/load/`.
- Create: dashboards under `infra/grafana/`.
- Create: alert rules under `infra/prometheus/`.
- Update: `docs/RUNBOOK.md` and backup/recovery docs.

### Targets

- Search p50 below 40 ms.
- Search p95 below 120 ms.
- Search p99 below 250 ms.
- Autocomplete p95 below 50 ms.
- AI simple response below 2 seconds.
- AI complex response below 5 seconds.
- Streaming begins below 500 ms where provider permits.
- 99.9% availability baseline.

### Acceptance criteria

- Load test covers 500 average QPS, 5,000 peak QPS, and controlled burst testing.
- Search latency and error budgets are measured by tenant and region.
- Worker restart does not lose outbox events.
- Database pool exhaustion and Redis failure are observable.
- Backup restore is tested, not merely configured.

### Complexity / impact

High complexity. High reliability and scale impact.

## P2 phase gate

- Personalization is opt-in and privacy-tested.
- Recommendations have offline evaluation.
- At least CSV, REST, webhooks, Shopify, WooCommerce, and Magento paths are tested according to released scope.
- Image search has real vector retrieval and deletion correctness.
- Analytics retention and reconciliation pass.
- Load, recovery, dashboards, and backup-restore tests pass.
- User approves P3 start.

---

# P3 — Future Improvements

## P3 outcome

Mercury supports enterprise deployment, marketplaces, advanced integrations, and sophisticated ranking/agent workflows.

## P3.1 — Search engine adapters

- Create: `app/infrastructure/search/base.py`.
- Create: `app/infrastructure/search/opensearch.py`.
- Create: `app/infrastructure/search/elasticsearch.py`.
- Keep: `app/infrastructure/search/typesense.py` as default adapter.
- Add adapter contract tests.
- Document feature differences and migration behavior.

Acceptance: identical public search contract across supported engines, with documented capability flags where engines differ.

## P3.2 — Marketplace and seller isolation

- Extend tenant -> store -> catalog -> seller hierarchy.
- Add seller ownership to canonical items, search documents, events, analytics, and permissions.
- Add seller-level filters and merchandising controls.
- Add seller onboarding and seller API keys.
- Test seller-to-seller and seller-to-merchant isolation.

Acceptance: seller cannot read or mutate another seller's catalog; merchant can aggregate according to policy.

## P3.3 — Enterprise identity and governance

- SAML SSO.
- SCIM provisioning.
- OIDC enterprise service accounts.
- RBAC with organization, store, catalog, seller, and feature scopes.
- Immutable audit logs.
- Key rotation and emergency revocation.
- Approval workflows for sensitive operations.

Acceptance: all privileged actions are authenticated, authorized, auditable, and testable.

## P3.4 — Deployment and compliance

- SaaS regional tenant placement.
- Private cloud deployment.
- Self-hosted package.
- Air-gapped deployment.
- Active-active multi-region design.
- SOC 2 evidence automation.
- ISO 27001 control mapping.
- Backup encryption and restore evidence.

Acceptance: documented deployment profiles use the same application APIs and pass security/recovery checks.

## P3.5 — Advanced commerce optimization

- Revenue-aware ranking.
- Margin-aware ranking.
- Inventory-aware ranking.
- Merchant objective configuration.
- Budget-constrained optimization.
- Counterfactual ranking evaluation.
- Fairness and bias monitoring.

Acceptance: objective changes are explainable, reversible, experimentable, and cannot bypass hard catalog constraints.

## P3.6 — MCP write workflows and agents

Only after P1 read-only MCP is stable and P3 governance exists:

- `create_draft_product`.
- `update_inventory`.
- `create_collection`.
- `create_merchandising_campaign`.
- Human approval workflows.
- Scoped service accounts.
- Dry-run mode.
- Full audit trail.
- Automatic rollback where possible.

Acceptance: no autonomous destructive mutation; every write has scope, approval state, actor, reason, and audit record.

## P3 complexity / impact

Very high complexity. Enterprise and long-term differentiation impact.

---

# 2. Standard Task Template

Every future implementation task must be written using this shape before coding:

```markdown
### Task ID: P1.1-T01

Objective: [one concrete outcome]

Files:
- Create: exact/path
- Modify: exact/path
- Test: exact/path
- Docs: exact/path

Dependencies:
- Previous task IDs.
- Existing interfaces.
- Migration or infrastructure prerequisites.

Risks:
- Security risk.
- Compatibility risk.
- Operational risk.

Acceptance criteria:
- Observable behavior 1.
- Observable behavior 2.
- Test command and expected result.

Complexity: Low | Medium | High
Impact: Low | Medium | High
```

Break large phase items into 2-5 minute implementation steps:

1. Add failing test.
2. Run focused test and confirm failure.
3. Implement minimal behavior.
4. Run focused test and confirm pass.
5. Run regression tests.
6. Update docs/OpenAPI.
7. Review security and tenant scope.
8. Commit one logical change.

---

# 3. Verification Commands

Run from repository root:

```bash
ruff check app tests alembic main.py
python -m compileall -q app main.py
pytest -q
docker compose config -q
docker compose -f docker-compose.prod.yml config -q
alembic heads
git diff --check
```

For external integration verification:

```bash
MERCURY_RUN_INTEGRATION=1 pytest -q tests/integration
```

For E2E verification:

```bash
MERCURY_E2E_URL=http://localhost:8000 pytest -q tests/e2e
```

Do not mark integration or E2E acceptance complete when the required services or URL are unavailable.

---

# 4. Definition of Done

A task is done only when:

- Code is implemented within existing architectural boundaries.
- Tenant scope is explicit and tested.
- Cache keys are tenant-safe.
- Errors and timeouts are handled.
- Public API behavior is documented.
- Migration exists for schema changes.
- Focused tests pass.
- Relevant regression tests pass.
- No new lint or type/runtime errors are introduced.
- Metrics/logging exist for operationally important behavior.
- Documentation is updated.

A phase is done only when its phase gate passes and the user approves moving to the next phase.

---

# 5. Recommended Execution Sequence

```text
P1.1 Read-only MCP
P1.2 AI provider abstraction
P1.3 Search quality and merchant controls
P1.4 Redis hardening
P1.5 Widget readiness
        |
P2.1 Personalization
P2.2 Recommendations
P2.3 Catalog integrations
P2.4 Image search
P2.5 Analytics
P2.6 Scale and operations
        |
P3.1 Search adapters
P3.2 Marketplace
P3.3 Enterprise identity
P3.4 Deployment/compliance
P3.5 Advanced optimization
P3.6 Governed MCP writes
```

No P2 feature should weaken P0 tenant isolation. No P3 enterprise feature should create a separate application architecture unless deployment isolation specifically requires it.

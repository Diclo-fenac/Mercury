# Locust Load-Test Hardening

## Purpose

Reproduce the Mercury search API failures seen under 50 concurrent Locust users,
identify whether they originate at the HTTP server, dependency pools, or the
search/embedding path, and harden the confirmed bottlenecks without changing
the public search API.

## Success criteria

- The application starts reliably in the load-test environment.
- A baseline and post-fix Locust run use 50 users, a 10-user/second spawn rate,
  and a 60-second duration.
- The post-fix run has no `RemoteDisconnected` or `ConnectionResetError`
  client failures, no server startup failure, and no HTTP 5xx responses caused
  by the load-related bottlenecks.
- Existing unit and integration tests continue to pass.
- The final report records request counts, failures, latency percentiles, and
  relevant application logs for both runs.

## Current evidence and constraints

- The working tree contains extensive user changes; implementation must avoid
  reverting or rewriting unrelated files.
- `entrypoint.sh` currently sets only workers and does not configure Uvicorn's
  backlog or concurrency limit.
- `main.py` configures a default executor but calls `asyncio.get_running_loop()`
  without importing the `asyncio` module.
- Redis is constructed with a 200-connection override in the container, while
  the client constructor default remains 20.
- `Settings` was configured for the retired `text-embedding-004` model, while the
  Gemini provider's fallback constant was `gemini-embedding-001`; the provider
  factory passes the settings value. The effective model must be tested and
  aligned with the supported `gemini-embedding-2` configuration.
- Docker is required for the full-stack run, and access may require explicit
  host permission in the execution environment.

## Design

### Baseline and diagnostics

Use the existing Compose stack and `tests/load/locustfile.py`. Start the
dependencies and API, wait for `/health`, then run Locust headlessly with the
approved 50-user, 10-user/second, 60-second profile. Save CSV statistics and
server logs outside the repository or in an ignored diagnostics directory.
Inspect failures by endpoint and correlate client connection errors with API
startup logs, Uvicorn worker exits, Redis pool errors, Typesense timeouts, and
embedding-provider errors.

### HTTP server capacity

Keep Uvicorn as the server and make its capacity controls configurable in
`entrypoint.sh`:

- `WORKERS`, default `2`;
- `BACKLOG`, default `2048`;
- `LIMIT_CONCURRENCY`, default `1000`.

Pass these values to Uvicorn while preserving the current host, port, and
uvloop settings. This avoids hard-coding deployment-specific values and
ensures the load-test container uses the intended socket queue and in-flight
request ceiling.

### Blocking dependency execution

Retain the synchronous Typesense SDK behind `run_in_executor`, but configure a
process-local `ThreadPoolExecutor` in the application lifespan. Add the missing
`asyncio` import and expose the worker count through a settings value with a
default of 200, so the default is explicit and testable. Do not create a new
executor per request or alter the Typesense adapter's public async methods.

### Redis and embedding configuration

Make the Redis pool capacity explicit at the container boundary and add focused
tests proving the configured pool receives the expected maximum. Preserve the
client's lower constructor default for callers that do not need high
concurrency.

Test the embedding factory's selected model. Use `gemini-embedding-2` with the
384-dimensional Typesense schema and omit the obsolete `task_type` option for
that model, while preserving mock/local fallback behavior when no valid API key
is available. No live Gemini call is required for this load test.

### Verification

Add unit-level regression tests for the Uvicorn environment expansion, lifespan
executor setup, Redis pool construction, and embedding model selection. Run the
focused tests, the normal test suite, and then the identical Locust profile
again. If the full stack cannot be started because Docker permission or an
external service remains unavailable, report that blocker with the completed
local evidence rather than weakening the load-test assertions.

## Non-goals

- Replacing the Typesense SDK with a new async search client.
- Changing search response schemas, authentication, rate-limit policy, or
  Locust request mix.
- Increasing database or Typesense server resources without evidence from the
  baseline.
- Hiding client failures with retries or by marking failed requests successful.

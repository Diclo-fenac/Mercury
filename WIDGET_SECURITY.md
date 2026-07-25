# Mercury Search Widget – Security Guide

> **Version 2.0** · For merchants, developers, and security reviewers

---

## ⚠️ Critical: Never Embed a Private Key

```
❌ WRONG — this gives your entire Mercury account access to anyone on the internet:

<script src="/widget/mercury-widget.min.js"
  data-api-key="sk_live_abc123_PRIVATE_ADMIN_KEY">  ← NEVER DO THIS
</script>

✅ CORRECT — only public keys belong in browser code:

<script src="/widget/mercury-widget.min.js"
  data-api-key="pk_live_abc123_PUBLIC_SEARCH_KEY">
</script>
```

**Public keys (`pk_*`) can only:**
- Search your product catalog
- Fetch widget configuration
- Submit anonymous click/search telemetry

**Public keys cannot:**
- Access admin APIs
- Read, modify, or delete catalog data
- Access other tenants' data
- Perform ingestion, user management, or analytics exports
- Access any secret, credential, or private field

---

## Key Types

| Key Prefix | Type | Used Where |
|---|---|---|
| `pk_live_…` | Public search key | Widget embed in storefront HTML |
| `sk_live_…` | Private admin key | Backend only — never in browser code |
| `pk_test_…` | Public test key | Development/staging environments |
| `sk_test_…` | Private test key | Backend tests only |

---

## Public API Boundary

The widget only calls these endpoints:

| Endpoint | Method | Auth | Purpose |
|---|---|---|---|
| `/api/v1/widget/search/instant` | GET | `X-API-Key: pk_*` | Instant product search |
| `/api/v1/widget/config` | GET | `X-API-Key: pk_*` | Branding config |
| `/api/v1/telemetry/events` | POST | `X-API-Key: pk_*` | Click/search events |

All other endpoints (admin, ingest, analytics, catalog management) **reject public keys** with `403 Forbidden`.

---

## Server-Side Domain Enforcement

### How it works

Mercury validates the request's `Origin` header against a per-tenant allowlist. This enforcement happens on the **server**, not in JavaScript (which can be bypassed). The widget sends its origin automatically with every cross-origin request.

### Configuration

In the Mercury dashboard, add your storefront domains:

```
https://www.mystore.com
https://staging.mystore.com
http://localhost:3000   ← for local development only
```

**Do not add `*`** — wildcard origins allow any website to use your search key.

### Test cases that must pass

| Scenario | Expected result |
|---|---|
| Valid domain (in allowlist) | ✅ 200 OK |
| Invalid domain (not in allowlist) | ❌ 403 Forbidden |
| Missing Origin header (same-origin) | ✅ 200 OK (same-origin requests don't send Origin) |
| `localhost` in development | ✅ 200 OK (if explicitly added to allowlist) |
| Revoked key | ❌ 401 Unauthorized |
| Malformed key | ❌ 401 Unauthorized |
| Cross-tenant key | ❌ 401/403 (server validates key-to-org binding) |

---

## XSS Prevention

The widget **never** uses `innerHTML`, `insertAdjacentHTML`, or `eval` with data received from the backend. All product fields are rendered as text nodes:

```js
// ✅ Safe — text node, no HTML interpretation
element.textContent = product.title;

// ❌ What the old widget did — never done in v2
element.innerHTML = `<h4>${product.title}</h4>`;  // REMOVED
```

Image and product URLs are validated:
```js
function isSafeUrl(url) {
  const parsed = new URL(url);
  return parsed.protocol === 'https:' || parsed.protocol === 'http:';
  // Rejects: javascript:, data:, vbscript:, file:, etc.
}
```

---

## Data Minimization (Telemetry)

The widget collects **only** the following telemetry data. No personal information is collected.

| Field | Value | Purpose |
|---|---|---|
| `event_type` | `widget_loaded`, `search_requested`, etc. | Event classification |
| `query` | Text typed by the user | Search analytics |
| `product_id` | Opaque product identifier | Click analytics |
| `search_id` | Server-generated search UUID | Click-to-search attribution |
| `session_id` | Anonymous random ID (per browser tab) | Session deduplication |
| `position` | Rank of clicked result | Relevance feedback |
| `timestamp` | ISO 8601 UTC | Time series analysis |

**What is never collected:**
- Name, email, address, phone, or any personal identifier
- Payment information
- Device fingerprint
- IP address (collected by the server, not the widget)
- Browsing history beyond the current search session

The anonymous session ID is stored in `sessionStorage` and is **not** persisted across browser sessions or shared across tabs.

---

## Content Security Policy (CSP)

If your storefront uses a Content Security Policy, add:

```
script-src  'self' https://your-mercury-instance.example;
connect-src 'self' https://your-mercury-instance.example;
img-src     'self' https: data:;
```

The widget does **not** load external scripts, fonts, or stylesheets (all styles are inlined in the Shadow DOM). No `unsafe-inline` or `unsafe-eval` is required.

---

## Error Response Safety

The widget never displays raw backend error messages. Safe messages are shown instead:

| Backend response | Widget displays |
|---|---|
| 429 Too Many Requests | "Too many requests. Please wait a moment and try again." |
| 401/403 Unauthorized | "Search unavailable. Please contact the store owner." |
| 500 Internal Server Error | "Search is temporarily unavailable. Please try again." |
| Network error | "Network error. Please check your connection." |

Stack traces, tenant IDs, database errors, and internal hostnames are **never** surfaced to the frontend.

---

## Upgrade Policy

- **Minor versions** (2.x) are backward-compatible within the same major version.
- **Major versions** may change the public key format, embed API, or CSS variable names. Migration guides will be published.
- Public keys do not expire automatically; revoke them from the Mercury dashboard if compromised.
- Always pin to a specific version URL in production rather than using a floating `/latest` URL.

```html
<!-- ✅ Pinned version -->
<script src="/widget/mercury-widget@2.0.0.min.js" ...>

<!-- ⚠️ Avoid floating references in production -->
<script src="/widget/mercury-widget.min.js" ...>
```

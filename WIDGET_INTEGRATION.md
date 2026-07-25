# Mercury Search Widget – Integration Guide

> **Version 2.0** · Last updated: July 2026

This guide explains how to add the Mercury Search widget to any storefront with a single script tag. No JavaScript framework, build tool, or NPM installation is required.

---

## Quick Start

### Option A — Script Tag (Recommended)

Copy and paste this snippet into your storefront's `<head>` or `<body>` before the closing `</body>` tag:

```html
<script
  src="https://your-mercury-instance.example/widget/mercury-widget.min.js"
  data-api-key="pk_your_public_search_key"
  data-endpoint="https://your-mercury-instance.example"
  defer>
</script>
```

The widget auto-mounts immediately after the script tag. No other setup is required.

---

### Option B — Programmatic Mount

Use this approach when you need to control the exact location of the widget, or when your site uses a JavaScript framework:

```html
<!-- 1. Load the widget script (no auto-mount if data-api-key is absent) -->
<script src="/widget/mercury-widget.min.js" defer></script>

<!-- 2. Add a container element -->
<div id="my-product-search"></div>

<!-- 3. Mount programmatically -->
<script>
  document.addEventListener('DOMContentLoaded', function () {
    var instance = window.MercurySearch.mount({
      target: '#my-product-search',
      apiKey: 'pk_your_public_search_key',
      endpoint: 'https://your-mercury-instance.example',
      placeholder: 'Search products…',
      limit: 8,
    });

    // To unmount later (e.g., on SPA route change):
    // instance.destroy();
  });
</script>
```

---

### Option C — Web Component (HTML native)

```html
<mercury-search
  style="--mercury-accent: #e11d48; display: block; max-width: 500px;"
></mercury-search>

<script src="/widget/mercury-widget.min.js" defer></script>
<script>
  document.querySelector('mercury-search').configure({
    apiKey: 'pk_xxx',
    endpoint: 'https://store.example',
  });
</script>
```

---

## Same-Origin vs Remote Endpoint

| Setup | `data-endpoint` value |
|---|---|
| Widget served from same server as Mercury | Omit — defaults to `window.location.origin` |
| Merchant site on a different domain | Full URL, e.g. `https://search.yourdomain.com` |

**CORS requirement:** When the endpoint is on a different origin, your Mercury backend must include the merchant's domain in its `ALLOWED_ORIGINS` setting.

---

## Installation Checklist

- [ ] Replace `pk_your_public_search_key` with your real public key (starts with `pk_`)
- [ ] Replace `https://your-mercury-instance.example` with your real Mercury URL
- [ ] Add your storefront domain to Mercury's allowed-domain list (see WIDGET_SECURITY.md)
- [ ] Test in your browser's DevTools Network tab: all widget requests should use `X-API-Key: pk_…`
- [ ] Verify no `sk_` key appears anywhere in your page source or network requests

---

## SPA / Turbo / HTMX Compatibility

If your site uses Turbo, HTMX, or a single-page app framework, call `destroy()` before page transitions and `mount()` again on the new page:

```js
// Turbo example
document.addEventListener('turbo:before-visit', function () {
  if (window.__mercuryInstance) {
    window.__mercuryInstance.destroy();
  }
});

document.addEventListener('turbo:load', function () {
  window.__mercuryInstance = window.MercurySearch.mount({
    target: '#search',
    apiKey: 'pk_xxx',
  });
});
```

---

## Demo Storefront

A complete demo page is available at:

```
https://your-mercury-instance.example/widget/demo.html
```

This page deliberately applies hostile CSS (global `all: unset` reset, `overflow: hidden` containers, high z-index headers) to verify widget isolation.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Widget not appearing | Missing `data-api-key` | Verify the script tag attribute exists and starts with `pk_` |
| Console error: "must start with pk_" | Admin key used in embed | Use a public key — see WIDGET_SECURITY.md |
| "Search unavailable" error | Invalid or revoked key | Generate a new public key in the Mercury dashboard |
| No results for any query | Domain not in allow-list | Add your site's origin in Mercury's domain settings |
| Widget styles look broken | Shadow DOM not supported | Check browser compatibility (requires Chrome 53+, Firefox 63+, Safari 10.1+) |
| CORS error in console | `data-endpoint` domain not in `ALLOWED_ORIGINS` | Add the endpoint to Mercury's CORS settings |
| Widget mounting twice | `mount()` called multiple times | `mount()` is idempotent on the same target; or call `destroy()` first |
| Dropdown appears behind header | z-index conflict | Widget uses `z-index: 2147483647` inside Shadow DOM — this should always be on top |

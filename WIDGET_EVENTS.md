# Mercury Search Widget – Events Reference

> **Version 2.0**

The widget fires DOM custom events and backend telemetry events. This document covers both.

---

## DOM Custom Events (Browser-side)

These events bubble up from the `<mercury-search>` element through the Shadow DOM boundary (`composed: true`) and can be listened to on any ancestor element.

### `mercury:result-selected`

Fired when a user clicks a search result that **does not have a product URL** (or when the merchant prefers to handle navigation). If the product has a valid URL, the widget navigates directly and does not fire this event.

```js
document.addEventListener('mercury:result-selected', function (e) {
  const { product, query, position } = e.detail;

  console.log('Product selected:', product);
  // product: { id, title, brand, category, price, inStock, imageUrl, productUrl }
  // query: string — the search query that produced this result
  // position: number — 1-indexed rank of the selected result
});
```

**Use case:** Custom SPA navigation, cart integration, analytics.

---

## Telemetry Events (Backend-side)

The widget automatically sends telemetry to `/api/v1/telemetry/events`. All events use the same payload shape.

### Event Payload Shape

```json
{
  "event_type": "search_result_clicked",
  "product_id": "prod_abc123",
  "query": "running shoes",
  "search_id": "srch_f8e2b1d4",
  "user_id": "ms_7f2x9k3p",
  "metadata": {
    "position": 2,
    "timestamp": "2026-07-25T11:00:00.000Z"
  }
}
```

### Event Types

| Event | When fired | Key fields |
|---|---|---|
| `widget_loaded` | Widget initializes successfully | — |
| `search_requested` | User starts a search (after debounce) | `query` |
| `search_results_received` | Backend responds with results | `query`, `metadata.count` |
| `search_no_results` | Backend returns zero results | `query` |
| `search_result_clicked` | User clicks a result | `product_id`, `query`, `search_id`, `metadata.position` |

### Privacy

All `user_id` values are anonymous session IDs generated per browser tab (format: `ms_<random>`). They do not contain personal information and are not persisted across sessions.

---

## Conversion Events (Merchant-implemented)

Optional conversion events (`add_to_cart`, `checkout_completed`) are **not** fired automatically by the widget — they depend on your storefront's own event system. Wire them up yourself after handling `mercury:result-selected`:

```js
// Example: add to cart and send telemetry
document.addEventListener('mercury:result-selected', async function (e) {
  const { product } = e.detail;

  // 1. Add to cart (your own store logic)
  await myCart.add(product.id, 1);

  // 2. Optionally send conversion telemetry to Mercury
  fetch('https://your-mercury-instance.example/api/v1/telemetry/events', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': 'pk_your_public_key',
    },
    body: JSON.stringify({
      event_type: 'add_to_cart',
      product_id: product.id,
      query: e.detail.query,
      user_id: null,  // pass an anonymous ID if available
    }),
  });
});
```

> **Note:** Do not use conversion telemetry if your analytics pipeline cannot correlate anonymous session IDs. Reporting inaccurate conversion data harms search relevance tuning.

---

## Deduplication

The widget deduplicates click events: if the same product is clicked within 300ms (e.g., double-click), only one telemetry event is fired.

---

## Delivery Mechanism

Click events use `navigator.sendBeacon` when available, ensuring telemetry is delivered even when the user navigates away immediately after clicking. A `fetch(..., { keepalive: true })` fallback is used in browsers without `sendBeacon`.

Telemetry never blocks navigation or throws errors that would affect the merchant page.

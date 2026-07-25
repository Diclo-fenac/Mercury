# Mercury Search Widget – Configuration Reference

> **Version 2.0**

---

## Script Tag Attributes

All configuration is supplied via `data-*` attributes on the script tag. No JavaScript is required for basic usage.

| Attribute | Required | Default | Description |
|---|---|---|---|
| `data-api-key` | ✅ Yes | — | Public search key starting with `pk_`. **Never use a private `sk_` key.** |
| `data-endpoint` | No | Same origin | Full URL of your Mercury instance, e.g. `https://search.example.com`. Omit to use the same server that hosts the widget. |
| `data-placeholder` | No | `Search products…` | Input placeholder text. Max 100 chars. |
| `data-theme` | No | `auto` | `auto` (respects `prefers-color-scheme`), `light`, or `dark`. |
| `data-limit` | No | `8` | Max results to display. Must be 1–50. |
| `data-min-length` | No | `2` | Minimum query characters before searching. Must be ≥ 1. |
| `data-debounce` | No | `200` | Milliseconds to wait after typing before firing search request. |
| `data-target` | No | After script tag | CSS selector for the element to mount the widget into. |

### Example with all attributes

```html
<script
  src="/widget/mercury-widget.min.js"
  data-api-key="pk_live_abc123xyz"
  data-endpoint="https://search.mystore.example"
  data-placeholder="What are you looking for?"
  data-theme="auto"
  data-limit="10"
  data-min-length="2"
  data-debounce="150"
  data-target="#site-search"
  defer>
</script>
```

---

## Programmatic API Options

When using `window.MercurySearch.mount(options)`:

```js
window.MercurySearch.mount({
  target:      '#site-search',   // Required: selector string or DOM element
  apiKey:      'pk_xxx',        // Required: public key
  endpoint:    'https://…',     // Optional: default same origin
  placeholder: 'Search…',      // Optional
  theme:       'auto',          // Optional: 'auto' | 'light' | 'dark'
  limit:       8,               // Optional: 1–50
  minLength:   2,               // Optional
  debounce:    200,             // Optional: milliseconds
});
```

**Returns:** `{ destroy: Function }` — call `instance.destroy()` to unmount.

---

## CSS Variable Theming

Apply these CSS custom properties to the `<mercury-search>` element (or its ancestor) to customize the widget's appearance. All variables are scoped inside the Shadow DOM and do **not** affect your merchant page.

```css
mercury-search {
  --mercury-accent:      #5b5ef7;       /* Primary color (buttons, focus ring, price) */
  --mercury-bg:          #ffffff;       /* Widget background */
  --mercury-text:        #111827;       /* Primary text color */
  --mercury-text-muted:  #6b7280;       /* Secondary text (brand, category) */
  --mercury-border:      #e5e7eb;       /* Border color */
  --mercury-hover:       #f9fafb;       /* Hover/selected row background */
  --mercury-error:       #dc2626;       /* Error state color */
  --mercury-success:     #16a34a;       /* In-stock badge color */
  --mercury-font:        system-ui, sans-serif; /* Font family */
  --mercury-radius:      8px;           /* Border radius */
  --mercury-shadow:      0 10px 40px -8px rgba(0, 0, 0, 0.15); /* Dropdown shadow */
}
```

### Dark Mode

The widget automatically switches to dark mode when `prefers-color-scheme: dark` is active, unless you set `data-theme="light"` to force light mode.

To force dark mode:
```css
mercury-search { --mercury-bg: #1e2435; --mercury-text: #f0f2f8; }
```

Or use `data-theme="dark"` attribute:
```html
<script src="…" data-api-key="pk_xxx" data-theme="dark" defer></script>
```

### Brand Color Examples

```css
/* Indigo (default) */
mercury-search { --mercury-accent: #5b5ef7; }

/* Rose */
mercury-search { --mercury-accent: #e11d48; --mercury-bg: #fff1f2; }

/* Emerald */
mercury-search { --mercury-accent: #059669; }

/* Orange */
mercury-search { --mercury-accent: #ea580c; }
```

---

## Width and Layout

The widget uses `display: block; width: 100%` and adapts to its container's width. Control width via the container:

```css
/* Constrain width */
#my-search-container {
  max-width: 480px;
  margin: 0 auto;
}
```

Or directly:
```css
mercury-search {
  max-width: 600px;
  display: block;
}
```

---

## Multiple Widgets

You can have multiple widgets on the same page with different configurations:

```html
<div id="header-search"></div>
<div id="category-search"></div>

<script>
  const headerWidget  = window.MercurySearch.mount({ target: '#header-search',   apiKey: 'pk_xxx', limit: 5 });
  const categoryWidget = window.MercurySearch.mount({ target: '#category-search', apiKey: 'pk_xxx', limit: 10, placeholder: 'Search this category…' });
</script>
```

Each widget instance is fully independent with its own state, listeners, and lifecycle.

---

## Remote Theme from Backend

When the widget loads, it fetches branding config from `/api/v1/widget/config` using the provided API key. This allows merchants to configure colors and placeholder text from the Mercury dashboard without touching their storefront code.

Backend config fields (set in Mercury dashboard):
- `widget_primary_color` — overrides `--mercury-accent`
- `widget_font_family` — overrides `--mercury-font`
- `widget_placeholder` — overrides the input placeholder

---

## Browser Support

| Browser | Min Version | Notes |
|---|---|---|
| Chrome / Edge | 80+ | Full support |
| Firefox | 75+ | Full support |
| Safari | 13+ | Full support |
| iOS Safari | 13+ | Full support (font size 16px prevents auto-zoom) |
| Opera | 67+ | Full support |
| IE 11 | ❌ Not supported | Shadow DOM requires polyfill (not included) |

> Shadow DOM v1 is required. The widget does **not** include a polyfill for older browsers. If IE 11 support is required, contact us for the polyfill bundle variant.

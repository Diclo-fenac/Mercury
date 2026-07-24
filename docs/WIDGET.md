# Mercury Storefront Widget

The Mercury Widget is a highly customizable, embeddable UI component that provides intelligent search, autocomplete, and an AI chat assistant directly on your storefront.

## Integration

To integrate the widget, include the script tag and initialize it on your storefront:

```html
<script src="https://<your-mercury-domain>/api/v1/widget/script.js?tenant=<your-organization-slug>"></script>

<div id="mercury-search-bar"></div>

<script>
  window.addEventListener('load', () => {
    window.MercuryWidget.init({
      container: '#mercury-search-bar',
      tenant: '<your-organization-slug>',
      mode: 'full', // 'minimal' or 'full' (includes AI chat)
      theme: {
        primary_color: '#6366f1',
        font_family: 'Inter, sans-serif'
      }
    });
  });
</script>
```

## Security & Tenant Isolation

The widget is securely isolated per tenant.
- It operates entirely within a Shadow DOM, preventing your site's CSS from conflicting with it, and preventing the widget's styles from leaking out.
- API keys embedded in the widget script are scoped exclusively to the `public_search` role.
- Tenant ID mapping strictly prevents cross-tenant data leakage. No products outside your organization will ever be rendered.

## Accessibility

The Mercury Widget conforms to WCAG 2.1 AA guidelines:
- Fully navigable via keyboard (Arrow keys, Enter, Escape).
- Uses accessible semantic HTML elements for dropdowns and modals.
- Proper focus management when opening the AI chat modal.

## Endpoints

- `GET /api/v1/widget/script.js`: Retrieves the bundled JavaScript for the widget.
- `GET /api/v1/widget/config`: Retrieves tenant-specific configuration such as colors and placeholders.

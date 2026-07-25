# Mercury Widget – Quick Integration Reference

For complete documentation, see:
- [WIDGET_INTEGRATION.md](./WIDGET_INTEGRATION.md) — Installation guide
- [WIDGET_CONFIGURATION.md](./WIDGET_CONFIGURATION.md) — All configuration options
- [WIDGET_SECURITY.md](./WIDGET_SECURITY.md) — Security guide (read before deploying)
- [WIDGET_EVENTS.md](./WIDGET_EVENTS.md) — Event hooks and telemetry

## Quickstart

```html
<script
  src="https://your-mercury-instance.example/widget/mercury-widget.min.js"
  data-api-key="pk_your_public_search_key"
  data-endpoint="https://your-mercury-instance.example"
  defer>
</script>
```

> ⚠️ **Never** embed a private (`sk_*`) key in storefront code. See [WIDGET_SECURITY.md](./WIDGET_SECURITY.md).

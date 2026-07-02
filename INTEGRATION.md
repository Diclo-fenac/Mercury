# Mercury Widget Integration

Copy and paste this snippet into your website's `<head>` or `<body>` tag:

```html
<script src="http://localhost:8000/widget/mercury-search.min.js"></script>
<script>
  window.addEventListener('load', () => {
    MercurySearch.init({
      apiKey: 'pk_YOUR_PUBLIC_SEARCH_KEY',
      apiBase: 'http://localhost:8000',
      selector: '.search-input'
    });
  });
</script>
```

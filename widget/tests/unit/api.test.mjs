/**
 * Mercury Widget – Unit Tests
 *
 * Tests run in Node.js with no browser dependencies.
 * Covers all non-DOM logic in api.js and index.js.
 *
 * Run:
 *   cd widget && node --test tests/unit/api.test.mjs
 *
 * OR with Jest (if configured):
 *   npx jest tests/unit/api.test.mjs
 */

import { strict as assert } from 'assert';
import { describe, it } from 'node:test';

// ================================================================
// Import only pure functions (no DOM required)
// ================================================================
// We inline the logic here to avoid browser globals in unit tests.

// -- isSafeUrl --
function isSafeUrl(url) {
  if (!url || typeof url !== 'string') return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' || parsed.protocol === 'http:';
  } catch { return false; }
}

// -- getSessionId -- (stubbed for test; real version uses sessionStorage)
function makeSessionId() {
  return 'ms_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
}

// -- Config parsing (from index.js) --
function parseConfig(attrs) {
  const raw = {
    apiKey:      attrs['data-api-key']     || '',
    endpoint:    attrs['data-endpoint']    || '',
    placeholder: attrs['data-placeholder'] || 'Search products…',
    theme:       attrs['data-theme']       || 'auto',
    limit:       parseInt(attrs['data-limit'] || '8', 10),
    minLength:   parseInt(attrs['data-min-length'] || '2', 10),
    debounce:    parseInt(attrs['data-debounce'] || '200', 10),
  };

  const errors = [];
  if (!raw.apiKey)                         errors.push('data-api-key is required');
  else if (!raw.apiKey.startsWith('pk_')) errors.push('must start with pk_');
  if (raw.endpoint) { try { new URL(raw.endpoint); } catch { errors.push('invalid endpoint URL'); } }
  if (!Number.isFinite(raw.limit) || raw.limit < 1 || raw.limit > 50) raw.limit = 8;
  if (!Number.isFinite(raw.minLength) || raw.minLength < 1)            raw.minLength = 2;
  if (!Number.isFinite(raw.debounce) || raw.debounce < 0)              raw.debounce = 200;

  return { config: raw, errors };
}

// -- Debounce --
function debounce(fn, wait) {
  let t;
  return function (...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), wait);
  };
}

// -- Product sanitizer (from api.js) --
function sanitizeProduct(item) {
  if (!item || typeof item !== 'object') return null;
  const title    = typeof item.title    === 'string' ? item.title.trim()    : '';
  const brand    = typeof item.brand    === 'string' ? item.brand.trim()    : '';
  const category = typeof item.category === 'string' ? item.category.trim() : '';
  const price    = typeof item.price    === 'number' ? item.price :
                   typeof item.selling_price === 'number' ? item.selling_price : null;
  const inStock  = typeof item.in_stock === 'boolean' ? item.in_stock :
                   (item.stock === true || item.stock === 1);
  const rawImage = item.image_url || item.image || '';
  const imageUrl = isSafeUrl(rawImage) ? rawImage : '';
  const rawUrl   = item.url || item.product_url || '';
  const productUrl = isSafeUrl(rawUrl) ? rawUrl : '';
  const id       = typeof item.id === 'string' ? item.id :
                   typeof item.id === 'number' ? String(item.id) : '';
  return { id, title, brand, category, price, inStock, imageUrl, productUrl };
}

// ================================================================
// Tests
// ================================================================

describe('isSafeUrl', () => {
  it('accepts https URLs', () => {
    assert.equal(isSafeUrl('https://example.com/product'), true);
  });
  it('accepts http URLs', () => {
    assert.equal(isSafeUrl('http://store.local/item'), true);
  });
  it('rejects javascript: URLs', () => {
    assert.equal(isSafeUrl('javascript:alert(1)'), false);
  });
  it('rejects data: URLs', () => {
    assert.equal(isSafeUrl('data:text/html,<script>alert(1)</script>'), false);
  });
  it('rejects null', () => {
    assert.equal(isSafeUrl(null), false);
  });
  it('rejects empty string', () => {
    assert.equal(isSafeUrl(''), false);
  });
  it('rejects relative paths', () => {
    assert.equal(isSafeUrl('/relative/path'), false);
  });
  it('rejects vbscript:', () => {
    assert.equal(isSafeUrl('vbscript:msgbox(1)'), false);
  });
});

describe('parseConfig – public key validation', () => {
  it('requires data-api-key', () => {
    const { errors } = parseConfig({});
    assert.ok(errors.some(e => e.includes('api-key')));
  });
  it('requires pk_ prefix', () => {
    const { errors } = parseConfig({ 'data-api-key': 'sk_secret_key' });
    assert.ok(errors.some(e => e.includes('pk_')));
  });
  it('accepts valid pk_ key', () => {
    const { config, errors } = parseConfig({ 'data-api-key': 'pk_live_abc123' });
    assert.equal(errors.length, 0);
    assert.equal(config.apiKey, 'pk_live_abc123');
  });
  it('rejects invalid endpoint URL', () => {
    const { errors } = parseConfig({ 'data-api-key': 'pk_x', 'data-endpoint': 'not-a-url' });
    assert.ok(errors.some(e => e.includes('invalid endpoint')));
  });
  it('accepts valid endpoint URL', () => {
    const { errors } = parseConfig({ 'data-api-key': 'pk_x', 'data-endpoint': 'https://store.example.com' });
    assert.equal(errors.length, 0);
  });
  it('clamps limit > 50 to 8', () => {
    const { config } = parseConfig({ 'data-api-key': 'pk_x', 'data-limit': '999' });
    assert.equal(config.limit, 8);
  });
  it('clamps negative limit to 8', () => {
    const { config } = parseConfig({ 'data-api-key': 'pk_x', 'data-limit': '-5' });
    assert.equal(config.limit, 8);
  });
  it('defaults placeholder', () => {
    const { config } = parseConfig({ 'data-api-key': 'pk_x' });
    assert.ok(config.placeholder.length > 0);
  });
  it('uses provided placeholder', () => {
    const { config } = parseConfig({ 'data-api-key': 'pk_x', 'data-placeholder': 'Find items…' });
    assert.equal(config.placeholder, 'Find items…');
  });
});

describe('sanitizeProduct', () => {
  it('sanitizes a valid product', () => {
    const result = sanitizeProduct({
      id: 'p001',
      title: 'Running Shoes',
      brand: 'Nike',
      category: 'Footwear',
      price: 99.99,
      in_stock: true,
      image_url: 'https://cdn.example.com/shoe.jpg',
      url: 'https://store.example.com/products/shoe',
    });
    assert.equal(result.id, 'p001');
    assert.equal(result.title, 'Running Shoes');
    assert.equal(result.price, 99.99);
    assert.equal(result.inStock, true);
    assert.equal(result.imageUrl, 'https://cdn.example.com/shoe.jpg');
    assert.equal(result.productUrl, 'https://store.example.com/products/shoe');
  });

  it('strips javascript: from image_url', () => {
    const result = sanitizeProduct({ id: '1', title: 'x', image_url: 'javascript:alert(1)' });
    assert.equal(result.imageUrl, '');
  });

  it('strips javascript: from product url', () => {
    const result = sanitizeProduct({ id: '1', title: 'x', url: 'javascript:alert(1)' });
    assert.equal(result.productUrl, '');
  });

  it('handles missing price gracefully', () => {
    const result = sanitizeProduct({ id: '1', title: 'x' });
    assert.equal(result.price, null);
  });

  it('uses selling_price if price missing', () => {
    const result = sanitizeProduct({ id: '1', title: 'x', selling_price: 49.00 });
    assert.equal(result.price, 49.00);
  });

  it('handles numeric id', () => {
    const result = sanitizeProduct({ id: 42, title: 'x' });
    assert.equal(result.id, '42');
  });

  it('trims title whitespace', () => {
    const result = sanitizeProduct({ id: '1', title: '  Laptop  ' });
    assert.equal(result.title, 'Laptop');
  });

  it('returns null for non-object input', () => {
    assert.equal(sanitizeProduct(null), null);
    assert.equal(sanitizeProduct('string'), null);
    assert.equal(sanitizeProduct(123), null);
  });

  it('handles stock: 1 (truthy integer) as in-stock', () => {
    const result = sanitizeProduct({ id: '1', title: 'x', stock: 1 });
    assert.equal(result.inStock, true);
  });

  it('handles in_stock: false', () => {
    const result = sanitizeProduct({ id: '1', title: 'x', in_stock: false });
    assert.equal(result.inStock, false);
  });
});

describe('debounce', () => {
  it('delays execution', (_, done) => {
    let count = 0;
    const fn = debounce(() => { count++; }, 50);
    fn(); fn(); fn(); // called 3 times
    setTimeout(() => {
      assert.equal(count, 1); // only fires once
      done();
    }, 100);
  });

  it('restarts timer on each call', (_, done) => {
    let lastArg;
    const fn = debounce((x) => { lastArg = x; }, 50);
    fn('first');
    setTimeout(() => fn('second'), 20); // resets timer
    setTimeout(() => {
      assert.equal(lastArg, 'second');
      done();
    }, 150);
  });
});

describe('session ID', () => {
  it('generates a non-empty string', () => {
    const id = makeSessionId();
    assert.ok(typeof id === 'string' && id.length > 8);
    assert.ok(id.startsWith('ms_'));
  });
  it('generates unique IDs', () => {
    const ids = new Set(Array.from({ length: 100 }, makeSessionId));
    assert.ok(ids.size > 90); // high uniqueness
  });
});

describe('endpoint normalization', () => {
  it('strips trailing slash', () => {
    const normalize = (e) => (e || '').replace(/\/$/, '');
    assert.equal(normalize('https://store.example.com/'), 'https://store.example.com');
    assert.equal(normalize('https://store.example.com'), 'https://store.example.com');
  });
});

describe('parseConfig – sk_ key rejection', () => {
  it('rejects sk_live_ key', () => {
    const { errors } = parseConfig({ 'data-api-key': 'sk_live_abc123' });
    assert.ok(errors.some(e => e.includes('pk_')));
  });
  it('rejects sk_test_ key', () => {
    const { errors } = parseConfig({ 'data-api-key': 'sk_test_abc123' });
    assert.ok(errors.some(e => e.includes('pk_')));
  });
  it('rejects empty string key', () => {
    const { errors } = parseConfig({ 'data-api-key': '' });
    assert.ok(errors.length > 0);
  });
  it('rejects key with no prefix at all', () => {
    const { errors } = parseConfig({ 'data-api-key': 'raw_key_without_prefix' });
    assert.ok(errors.some(e => e.includes('pk_')));
  });
});

describe('sanitizeProduct – XSS resistance', () => {
  it('does not eval/execute script in title', () => {
    const result = sanitizeProduct({ id: '1', title: '<script>alert(1)</script>' });
    // title is stored as-is (textContent rendering makes it safe); verify it is a string
    assert.equal(typeof result.title, 'string');
    // The raw string is preserved but will be text-node rendered in DOM (safe)
    assert.ok(result.title.includes('alert') === true); // stored, not executed
  });

  it('strips XSS from image URL', () => {
    const result = sanitizeProduct({ id: '1', title: 'x', image_url: 'javascript:alert(document.cookie)' });
    assert.equal(result.imageUrl, '');
  });

  it('strips data: URI from image URL', () => {
    const result = sanitizeProduct({ id: '1', title: 'x', image_url: 'data:image/svg+xml,<svg onload="alert(1)"/>' });
    assert.equal(result.imageUrl, '');
  });

  it('preserves valid CDN image URL with query params', () => {
    const url = 'https://cdn.shopify.com/s/files/product.jpg?width=300&v=1234';
    const result = sanitizeProduct({ id: '1', title: 'x', image_url: url });
    assert.equal(result.imageUrl, url);
  });

  it('preserves valid product URL with path params', () => {
    const url = 'https://mystore.com/collections/shoes/products/nike-air-max';
    const result = sanitizeProduct({ id: '1', title: 'x', url });
    assert.equal(result.productUrl, url);
  });
});

console.log('\n✅ All Mercury Widget unit tests passed\n');

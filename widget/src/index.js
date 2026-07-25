/**
 * Mercury Search Widget – Entry Point
 * Zero-dependency, Shadow DOM-isolated, script-tag-installable search widget.
 *
 * Embed:
 *   <script src="/widget/mercury-widget.js"
 *           data-api-key="pk_xxx"
 *           data-endpoint="https://store.example"
 *           defer>
 *   </script>
 *
 * Or programmatically:
 *   window.MercurySearch.mount({ target: '#my-search', apiKey: 'pk_xxx' });
 */

import { MercurySearchElement } from './ui.js';

// ------------------------------------------------------------------
// 1. Register the Web Component (idempotent)
// ------------------------------------------------------------------
if (!customElements.get('mercury-search')) {
  customElements.define('mercury-search', MercurySearchElement);
}

// ------------------------------------------------------------------
// 2. Config parsing – hardened
// ------------------------------------------------------------------
function parseConfig(script) {
  const raw = {
    apiKey:      script.getAttribute('data-api-key')      || '',
    endpoint:    script.getAttribute('data-endpoint')     || '',
    placeholder: script.getAttribute('data-placeholder')  || 'Search products…',
    theme:       script.getAttribute('data-theme')        || 'auto',
    limit:       parseInt(script.getAttribute('data-limit') || '8', 10),
    minLength:   parseInt(script.getAttribute('data-min-length') || '2', 10),
    debounce:    parseInt(script.getAttribute('data-debounce') || '200', 10),
    target:      script.getAttribute('data-target')       || '',
  };

  const errors = [];

  if (!raw.apiKey) {
    errors.push('data-api-key is required');
  } else if (!raw.apiKey.startsWith('pk_')) {
    errors.push('data-api-key must be a public key starting with pk_');
  }

  if (raw.endpoint) {
    try { new URL(raw.endpoint); } catch { errors.push('data-endpoint is not a valid URL'); }
  }

  if (!Number.isFinite(raw.limit) || raw.limit < 1 || raw.limit > 50) raw.limit = 8;
  if (!Number.isFinite(raw.minLength) || raw.minLength < 1) raw.minLength = 2;
  if (!Number.isFinite(raw.debounce) || raw.debounce < 0) raw.debounce = 200;

  return { config: raw, errors };
}

// ------------------------------------------------------------------
// 3. Script-tag auto-mount
// ------------------------------------------------------------------
function autoMount() {
  // Find *this* script tag – works with defer, type=module, and classic script.
  const scripts = document.querySelectorAll(
    'script[data-api-key], script[src*="mercury-widget"]'
  );

  let found = null;
  for (const s of scripts) {
    if (s.getAttribute('data-api-key')) { found = s; break; }
  }
  if (!found) return;

  const { config, errors } = parseConfig(found);

  if (errors.length) {
    if (typeof console !== 'undefined') {
      // Only warn in debug/dev; never throw uncaught errors.
      console.warn('[MercurySearch] Configuration error(s):', errors.join('; '));
    }
    return;
  }

  // Determine mount target
  let targetEl = null;
  if (config.target) {
    targetEl = document.querySelector(config.target);
    if (!targetEl) {
      console.warn('[MercurySearch] data-target selector "' + config.target + '" not found; inserting after script tag.');
    }
  }

  if (!targetEl) {
    // Insert a <mercury-search> element right after this script tag
    const el = document.createElement('mercury-search');
    found.parentNode.insertBefore(el, found.nextSibling);
    targetEl = el;
  }

  _mountOnElement(targetEl, config);
}

// ------------------------------------------------------------------
// 4. _mountOnElement – shared logic
// ------------------------------------------------------------------
function _mountOnElement(el, config) {
  // Idempotency: skip if already mounted
  if (el._mercuryMounted) return;
  el._mercuryMounted = true;

  // If element is not mercury-search, wrap it
  let host = el;
  if (el.tagName.toLowerCase() !== 'mercury-search') {
    host = document.createElement('mercury-search');
    el.appendChild(host);
  }

  // Pass config into the custom element
  host._mercuryConfig = config;
  // If already upgraded (already in DOM), call configure
  if (typeof host.configure === 'function') {
    host.configure(config);
  }
  // else: connectedCallback will call configure via _mercuryConfig
}

// ------------------------------------------------------------------
// 5. Public API: window.MercurySearch
// ------------------------------------------------------------------
const MercurySearch = {
  _instances: new Map(),

  /**
   * Programmatic mount.
   * @param {object} options - { target, apiKey, endpoint, placeholder, theme, limit }
   * @returns {{ destroy: Function }}
   */
  mount(options = {}) {
    const errors = [];
    const config = {
      apiKey:      options.apiKey      || '',
      endpoint:    options.endpoint    || '',
      placeholder: options.placeholder || 'Search products…',
      theme:       options.theme       || 'auto',
      limit:       options.limit       || 8,
      minLength:   options.minLength   || 2,
      debounce:    options.debounce    || 200,
    };

    if (!config.apiKey) errors.push('apiKey is required');
    else if (!config.apiKey.startsWith('pk_')) errors.push('apiKey must start with pk_');

    if (errors.length) {
      console.warn('[MercurySearch] mount() error:', errors.join('; '));
      return { destroy: () => {} };
    }

    let targetEl = null;
    if (options.target) {
      targetEl = typeof options.target === 'string'
        ? document.querySelector(options.target)
        : options.target;
    }

    if (!targetEl) {
      console.warn('[MercurySearch] mount() requires a valid target element or selector');
      return { destroy: () => {} };
    }

    // Idempotency: if already mounted on this element, destroy first
    if (targetEl._mercuryInstance) {
      targetEl._mercuryInstance.destroy();
    }

    const host = document.createElement('mercury-search');
    host._mercuryConfig = config;
    targetEl.appendChild(host);

    const instance = {
      destroy() {
        if (typeof host.destroy === 'function') host.destroy();
        host.remove();
        targetEl._mercuryInstance = null;
      }
    };

    targetEl._mercuryInstance = instance;
    return instance;
  },

  /**
   * Destroy all mounted widgets.
   */
  destroyAll() {
    document.querySelectorAll('mercury-search').forEach(el => {
      if (typeof el.destroy === 'function') el.destroy();
      el.remove();
    });
  },

  version: '2.0.0',
};

// Expose globally (one name, one namespace)
if (typeof window !== 'undefined') {
  window.MercurySearch = MercurySearch;
}

// ------------------------------------------------------------------
// 6. Auto-initialize
// ------------------------------------------------------------------
if (typeof document !== 'undefined') {
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', autoMount, { once: true });
  } else {
    autoMount();
  }
}

export { MercurySearch };

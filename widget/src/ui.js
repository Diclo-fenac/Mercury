/**
 * Mercury Search Widget – Shadow DOM UI Component
 *
 * Implements a <mercury-search> Web Component with:
 * - Full Shadow DOM CSS isolation
 * - Accessible combobox/listbox pattern
 * - Keyboard navigation (Arrow, Enter, Escape, Tab)
 * - Debounced search with AbortController
 * - Safe text rendering (no innerHTML with untrusted data)
 * - Loading, no-results, error, and offline states
 * - Click telemetry (non-blocking)
 * - WCAG AA focus indicators, ARIA attributes
 * - Viewport-aware dropdown positioning
 * - prefers-reduced-motion support
 * - CSS variable theming via :host
 * - Lifecycle: destroy() cleans up all listeners/timers/requests
 */

import css from './styles.css';
import { SearchAPI, MercuryApiError, ApiErrorType, getSessionId } from './api.js';

// ------------------------------------------------------------------
// Safe text helpers – never use innerHTML with untrusted values
// ------------------------------------------------------------------
function setText(el, text) {
  el.textContent = typeof text === 'string' ? text : String(text ?? '');
}

function createEl(tag, attrs = {}, textContent) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === 'className') el.className = v;
    else if (k === 'role' || k === 'aria-label' || k === 'aria-expanded' ||
             k === 'aria-activedescendant' || k === 'aria-controls' ||
             k === 'aria-selected' || k === 'aria-live' || k === 'aria-atomic' ||
             k === 'aria-busy' || k === 'aria-haspopup' || k === 'aria-autocomplete') {
      el.setAttribute(k, v);
    } else {
      el[k] = v;
    }
  }
  if (textContent !== undefined) setText(el, textContent);
  return el;
}

// ------------------------------------------------------------------
// Debounce
// ------------------------------------------------------------------
function debounce(fn, wait) {
  let t;
  return function (...args) {
    clearTimeout(t);
    t = setTimeout(() => fn.apply(this, args), wait);
  };
}

// ------------------------------------------------------------------
// MercurySearchElement – the Web Component
// ------------------------------------------------------------------
export class MercurySearchElement extends HTMLElement {
  constructor() {
    super();
    this._shadow = this.attachShadow({ mode: 'open' });
    this._api = null;
    this._config = null;
    this._state = {
      query: '',
      results: [],
      selectedIndex: -1,
      isLoading: false,
      isOpen: false,
      error: null,   // null | string (safe message)
      searchId: null,
    };
    this._sessionId = getSessionId();
    this._listeners = []; // { target, type, fn, opts? }
    this._timers = [];
    this._debounceSearch = null;
    this._lastClickedProductId = null; // for dedup
    this._lastClickTs = 0;
    this._els = {};
  }

  // ------------------------------------------------------------------
  // Web Component lifecycle
  // ------------------------------------------------------------------
  connectedCallback() {
    // Config may have been set by index.js before connectedCallback
    if (this._mercuryConfig) {
      this.configure(this._mercuryConfig);
    }
  }

  disconnectedCallback() {
    this.destroy();
  }

  // ------------------------------------------------------------------
  // Public API
  // ------------------------------------------------------------------

  configure(config) {
    if (this._config) return; // already configured (idempotent)
    this._config = config;
    this._api = new SearchAPI(config.endpoint, config.apiKey);
    this._debounceSearch = debounce(this._executeSearch.bind(this), config.debounce || 200);

    this._buildShadow();
    this._bindEvents();
    this._sendTelemetry({ event: 'widget_loaded' });

    // Optionally fetch remote theme override (non-blocking)
    this._api.getWidgetConfig().then(cfg => {
      if (cfg) this._applyRemoteTheme(cfg);
    });
  }

  destroy() {
    // Cancel requests
    if (this._api) this._api.cancelSearch();

    // Clear listeners
    for (const { target, type, fn, opts } of this._listeners) {
      target.removeEventListener(type, fn, opts);
    }
    this._listeners = [];

    // Clear timers
    for (const id of this._timers) clearTimeout(id);
    this._timers = [];

    // Clear shadow DOM
    this._shadow.innerHTML = '';
    this._els = {};
    this._config = null;
    this._api = null;
  }

  // ------------------------------------------------------------------
  // Shadow DOM construction
  // ------------------------------------------------------------------
  _buildShadow() {
    const shadow = this._shadow;
    shadow.innerHTML = '';

    // Styles (scoped inside shadow)
    const styleEl = document.createElement('style');
    styleEl.textContent = css;
    shadow.appendChild(styleEl);

    // Host wrapper (block, no layout shift)
    const wrapper = createEl('div', { className: 'mw-wrapper' });

    // --- Input row ---
    const inputRow = createEl('div', { className: 'mw-input-row' });

    // Visually hidden label for accessibility
    const label = createEl('label', {
      className: 'mw-label',
      htmlFor: 'mw-input',
    }, 'Search products');

    // Search icon
    const searchIcon = this._makeSearchIcon();

    // Input
    const input = createEl('input', {
      id: 'mw-input',
      type: 'search',
      className: 'mw-input',
      autocomplete: 'off',
      autocorrect: 'off',
      autocapitalize: 'off',
      spellcheck: false,
      'role': 'combobox',
      'aria-expanded': 'false',
      'aria-haspopup': 'listbox',
      'aria-autocomplete': 'list',
      'aria-controls': 'mw-listbox',
      'aria-activedescendant': '',
    });
    setText(input, '');
    input.placeholder = this._config.placeholder;
    input.setAttribute('enterkeyhint', 'search');

    // Clear button (hidden until text)
    const clearBtn = createEl('button', {
      className: 'mw-clear-btn mw-hidden',
      type: 'button',
      'aria-label': 'Clear search',
    });
    clearBtn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';

    inputRow.appendChild(label);
    inputRow.appendChild(searchIcon);
    inputRow.appendChild(input);
    inputRow.appendChild(clearBtn);

    // --- Status (ARIA live region) ---
    const status = createEl('div', {
      className: 'mw-status',
      role: 'status',
      'aria-live': 'polite',
      'aria-atomic': 'true',
    });

    // --- Dropdown listbox ---
    const dropdown = createEl('div', {
      id: 'mw-listbox',
      className: 'mw-dropdown',
      role: 'listbox',
      'aria-label': 'Search results',
    });
    dropdown.setAttribute('aria-hidden', 'true');

    wrapper.appendChild(inputRow);
    wrapper.appendChild(status);
    wrapper.appendChild(dropdown);
    shadow.appendChild(wrapper);

    this._els = { input, clearBtn, status, dropdown, wrapper };
  }

  _makeSearchIcon() {
    const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    icon.setAttribute('class', 'mw-search-icon');
    icon.setAttribute('viewBox', '0 0 24 24');
    icon.setAttribute('aria-hidden', 'true');
    icon.setAttribute('focusable', 'false');
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.setAttribute('d', 'M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z');
    path.setAttribute('stroke', 'currentColor');
    path.setAttribute('stroke-width', '2');
    path.setAttribute('stroke-linecap', 'round');
    path.setAttribute('fill', 'none');
    icon.appendChild(path);
    return icon;
  }

  // ------------------------------------------------------------------
  // Remote theme
  // ------------------------------------------------------------------
  _applyRemoteTheme(cfg) {
    const overrides = [];
    const safeColor = (v) => (typeof v === 'string' && /^#[0-9a-fA-F]{3,8}$|^rgba?\(|^hsl/.test(v)) ? v : null;
    const safeFontFamily = (v) => (typeof v === 'string' && v.length < 200) ? v : null;

    const c = safeColor(cfg.widget_primary_color);
    if (c) overrides.push(`--mercury-accent: ${c};`);

    const f = safeFontFamily(cfg.widget_font_family);
    if (f) overrides.push(`--mercury-font: ${f}, system-ui, sans-serif;`);

    const ph = typeof cfg.widget_placeholder === 'string' ? cfg.widget_placeholder : null;
    if (ph && this._els.input) this._els.input.placeholder = ph.slice(0, 100);

    if (overrides.length) {
      const extra = document.createElement('style');
      extra.textContent = `:host { ${overrides.join(' ')} }`;
      this._shadow.appendChild(extra);
    }
  }

  // ------------------------------------------------------------------
  // Event binding (all tracked for cleanup)
  // ------------------------------------------------------------------
  _on(target, type, fn, opts) {
    target.addEventListener(type, fn, opts);
    this._listeners.push({ target, type, fn, opts });
  }

  _bindEvents() {
    const { input, clearBtn, dropdown } = this._els;

    // Input typing → debounced search
    this._on(input, 'input', () => {
      const val = input.value;
      if (val !== this._state.query) {
        this._state.query = val;
        this._state.selectedIndex = -1;
        if (!val.trim() || val.trim().length < (this._config.minLength || 2)) {
          this._closeDropdown();
          this._clearStatus();
          this._updateClearBtn();
          return;
        }
        this._updateClearBtn();
        this._debounceSearch(val.trim());
      }
    });

    // Keyboard navigation (not debounced)
    this._on(input, 'keydown', (e) => this._handleKeydown(e));

    // Focus → reopen if query exists
    this._on(input, 'focus', () => {
      if (this._state.query.trim().length >= (this._config.minLength || 2) && this._state.results.length) {
        this._openDropdown();
      }
    });

    // Clear button
    this._on(clearBtn, 'click', () => {
      input.value = '';
      this._state.query = '';
      this._state.results = [];
      this._state.selectedIndex = -1;
      this._closeDropdown();
      this._clearStatus();
      this._updateClearBtn();
      input.focus();
    });

    // Close on outside click (document-level, with cleanup path)
    const outsideClick = (e) => {
      if (!this.contains(e.target) && !this._shadow.contains(e.target)) {
        this._closeDropdown();
      }
    };
    this._on(document, 'click', outsideClick, true);

    // Keyboard: Escape globally when open
    const globalEsc = (e) => {
      if (e.key === 'Escape' && this._state.isOpen) {
        this._closeDropdown();
        input.focus();
      }
    };
    this._on(document, 'keydown', globalEsc, true);

    // Dropdown click delegation
    this._on(dropdown, 'click', (e) => {
      const item = e.target.closest('[role="option"]');
      if (item) {
        const idx = parseInt(item.dataset.index, 10);
        if (Number.isFinite(idx)) this._selectResult(idx);
      }
    });

    // Prevent focus leaving shadow (Tab behavior: don't trap)
    this._on(dropdown, 'mousedown', (e) => {
      // Prevent input blur when clicking results
      e.preventDefault();
    });
  }

  // ------------------------------------------------------------------
  // Keyboard handler
  // ------------------------------------------------------------------
  _handleKeydown(e) {
    const { results, selectedIndex, isOpen } = this._state;
    const count = results.length;

    switch (e.key) {
      case 'ArrowDown':
        if (!isOpen && count) { this._openDropdown(); return; }
        if (!count) return;
        e.preventDefault();
        this._setSelected(selectedIndex < count - 1 ? selectedIndex + 1 : 0);
        break;

      case 'ArrowUp':
        if (!isOpen || !count) return;
        e.preventDefault();
        this._setSelected(selectedIndex > 0 ? selectedIndex - 1 : count - 1);
        break;

      case 'Enter':
        e.preventDefault();
        if (isOpen && selectedIndex >= 0 && selectedIndex < count) {
          this._selectResult(selectedIndex);
        } else if (this._state.query.trim().length >= (this._config.minLength || 2)) {
          // Execute search immediately (bypass debounce)
          this._executeSearch(this._state.query.trim());
        }
        break;

      case 'Tab':
        // Don't trap; let natural tab order proceed, just close dropdown
        if (isOpen) this._closeDropdown();
        break;

      // Escape handled at document level
    }
  }

  _setSelected(idx) {
    this._state.selectedIndex = idx;
    this._updateSelectionDOM();

    const { input } = this._els;
    const itemId = idx >= 0 ? `mw-opt-${idx}` : '';
    input.setAttribute('aria-activedescendant', itemId);
  }

  _updateSelectionDOM() {
    const { dropdown } = this._els;
    const items = dropdown.querySelectorAll('[role="option"]');
    items.forEach((el, i) => {
      const selected = i === this._state.selectedIndex;
      el.setAttribute('aria-selected', selected ? 'true' : 'false');
      el.classList.toggle('mw-selected', selected);
      if (selected) {
        el.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
      }
    });
  }

  // ------------------------------------------------------------------
  // Search execution
  // ------------------------------------------------------------------
  async _executeSearch(query) {
    if (!query || query.length < (this._config.minLength || 2)) return;

    this._state.isLoading = true;
    this._state.error = null;
    this._state.selectedIndex = -1;
    this._renderLoading();
    this._openDropdown();
    this._announceStatus('Searching…');
    this._sendTelemetry({ event: 'search_requested', query });

    try {
      const { results, searchId } = await this._api.search(query, this._config.limit || 8);

      // Race protection: ignore if query changed while awaiting
      if (query !== this._state.query.trim()) return;

      this._state.isLoading = false;
      this._state.results = results.filter(Boolean);
      this._state.searchId = searchId;
      this._renderResults();

      const count = this._state.results.length;
      if (count === 0) {
        this._announceStatus(`No results for "${query}"`);
        this._sendTelemetry({ event: 'search_no_results', query });
      } else {
        this._announceStatus(`${count} result${count === 1 ? '' : 's'} found`);
        this._sendTelemetry({ event: 'search_results_received', query, metadata: { count } });
      }
    } catch (err) {
      if (err instanceof MercuryApiError && err.type === ApiErrorType.ABORT) return;

      // Only update if query still matches
      if (query !== this._state.query.trim()) return;

      this._state.isLoading = false;
      this._state.error = err instanceof MercuryApiError ? err.message : 'Search unavailable. Please try again.';
      this._renderError(this._state.error);
      this._announceStatus(this._state.error);
    }
  }

  // ------------------------------------------------------------------
  // Result selection
  // ------------------------------------------------------------------
  _selectResult(idx) {
    const item = this._state.results[idx];
    if (!item) return;

    // Dedup: ignore double-fire within 300ms on same product
    const now = Date.now();
    if (this._lastClickedProductId === item.id && now - this._lastClickTs < 300) return;
    this._lastClickedProductId = item.id;
    this._lastClickTs = now;

    // Navigate to product URL if available
    if (item.productUrl) {
      // Fire telemetry before navigation
      this._sendTelemetry({
        event: 'search_result_clicked',
        query: this._state.query,
        productId: item.id,
        searchId: this._state.searchId,
        sessionId: this._sessionId,
        position: idx + 1,
      });
      // Navigate (telemetry uses sendBeacon so it doesn't block)
      window.location.href = item.productUrl;
    } else {
      // Dispatch a custom event for merchant to handle
      this._sendTelemetry({
        event: 'search_result_clicked',
        query: this._state.query,
        productId: item.id,
        searchId: this._state.searchId,
        sessionId: this._sessionId,
        position: idx + 1,
      });

      this.dispatchEvent(new CustomEvent('mercury:result-selected', {
        bubbles: true,
        composed: true, // crosses shadow boundary
        detail: { product: item, query: this._state.query, position: idx + 1 },
      }));
    }

    this._closeDropdown();
  }

  // ------------------------------------------------------------------
  // Dropdown open/close
  // ------------------------------------------------------------------
  _openDropdown() {
    if (this._state.isOpen) return;
    this._state.isOpen = true;
    const { dropdown, input } = this._els;
    dropdown.classList.add('mw-open');
    dropdown.setAttribute('aria-hidden', 'false');
    input.setAttribute('aria-expanded', 'true');
    this._positionDropdown();
  }

  _closeDropdown() {
    this._state.isOpen = false;
    this._state.selectedIndex = -1;
    const { dropdown, input } = this._els;
    dropdown.classList.remove('mw-open');
    dropdown.setAttribute('aria-hidden', 'true');
    input.setAttribute('aria-expanded', 'false');
    input.setAttribute('aria-activedescendant', '');
  }

  /**
   * Flip dropdown above input if not enough space below.
   */
  _positionDropdown() {
    const { dropdown, wrapper } = this._els;
    const rect = wrapper.getBoundingClientRect();
    const spaceBelow = window.innerHeight - rect.bottom;
    const spaceAbove = rect.top;

    if (spaceBelow < 200 && spaceAbove > spaceBelow) {
      dropdown.classList.add('mw-flip');
    } else {
      dropdown.classList.remove('mw-flip');
    }
  }

  // ------------------------------------------------------------------
  // Rendering helpers (all safe – no innerHTML with untrusted data)
  // ------------------------------------------------------------------
  _renderLoading() {
    const { dropdown } = this._els;
    dropdown.innerHTML = '';

    const msg = createEl('div', { className: 'mw-state-msg', 'aria-busy': 'true' });
    const spinner = createEl('span', { className: 'mw-spinner', 'aria-hidden': 'true' });
    msg.appendChild(spinner);
    msg.appendChild(document.createTextNode(' Searching…'));
    dropdown.appendChild(msg);
    this._openDropdown();
  }

  _renderError(safeMsg) {
    const { dropdown } = this._els;
    dropdown.innerHTML = '';
    const msg = createEl('div', { className: 'mw-state-msg mw-state-error' }, safeMsg);
    dropdown.appendChild(msg);
  }

  _renderResults() {
    const { dropdown } = this._els;
    const { results } = this._state;
    dropdown.innerHTML = '';

    if (results.length === 0) {
      const msg = createEl('div', { className: 'mw-state-msg mw-state-empty' });
      setText(msg, 'No products found for "');
      const q = createEl('strong');
      setText(q, this._state.query);
      msg.appendChild(q);
      msg.appendChild(document.createTextNode('"'));

      const hint = createEl('p', { className: 'mw-empty-hint' }, 'Try different keywords or browse all categories.');
      msg.appendChild(hint);
      dropdown.appendChild(msg);
      return;
    }

    results.forEach((item, idx) => {
      const option = this._buildResultItem(item, idx);
      dropdown.appendChild(option);
    });

    this._updateSelectionDOM();
  }

  _buildResultItem(item, idx) {
    // All values rendered as text nodes – never innerHTML
    const option = createEl('div', {
      className: 'mw-result-item',
      role: 'option',
      id: `mw-opt-${idx}`,
      'aria-selected': 'false',
    });
    option.dataset.index = String(idx);

    // Image (fixed dimensions to prevent layout shift)
    const imgWrapper = createEl('div', { className: 'mw-img-wrap' });
    if (item.imageUrl) {
      const img = createEl('img', {
        className: 'mw-img',
        alt: item.title || 'Product image',
        loading: 'lazy',
        decoding: 'async',
        width: '48',
        height: '48',
      });
      img.src = item.imageUrl;
      img.addEventListener('error', () => {
        imgWrapper.removeChild(img);
        const placeholder = createEl('div', { className: 'mw-img-placeholder', 'aria-hidden': 'true' }, '🛍');
        imgWrapper.appendChild(placeholder);
      });
      imgWrapper.appendChild(img);
    } else {
      const placeholder = createEl('div', { className: 'mw-img-placeholder', 'aria-hidden': 'true' }, '🛍');
      imgWrapper.appendChild(placeholder);
    }

    // Content
    const content = createEl('div', { className: 'mw-result-content' });

    const titleEl = createEl('div', { className: 'mw-result-title' });
    setText(titleEl, item.title || 'Unknown Product');

    const meta = createEl('div', { className: 'mw-result-meta' });
    if (item.brand || item.category) {
      setText(meta, [item.brand, item.category].filter(Boolean).join(' · '));
    }

    content.appendChild(titleEl);
    if (item.brand || item.category) content.appendChild(meta);

    // Price + availability
    const right = createEl('div', { className: 'mw-result-right' });

    if (item.price !== null && item.price !== undefined) {
      const price = createEl('div', { className: 'mw-result-price' });
      setText(price, '$' + Number(item.price).toFixed(2));
      right.appendChild(price);
    }

    const avail = createEl('div', {
      className: 'mw-result-avail ' + (item.inStock ? 'mw-instock' : 'mw-outstock'),
    });
    setText(avail, item.inStock ? 'In stock' : 'Out of stock');
    right.appendChild(avail);

    option.appendChild(imgWrapper);
    option.appendChild(content);
    option.appendChild(right);

    return option;
  }

  // ------------------------------------------------------------------
  // Status (ARIA live region)
  // ------------------------------------------------------------------
  _announceStatus(msg) {
    const { status } = this._els;
    if (!status) return;
    // Clear and re-set to ensure re-announcement
    setText(status, '');
    const t = setTimeout(() => setText(status, msg), 50);
    this._timers.push(t);
  }

  _clearStatus() {
    const { status } = this._els;
    if (status) setText(status, '');
  }

  // ------------------------------------------------------------------
  // Clear button visibility
  // ------------------------------------------------------------------
  _updateClearBtn() {
    const { clearBtn, input } = this._els;
    const hasText = input.value.length > 0;
    clearBtn.classList.toggle('mw-hidden', !hasText);
  }

  // ------------------------------------------------------------------
  // Telemetry (non-blocking, non-throwing)
  // ------------------------------------------------------------------
  _sendTelemetry(payload) {
    try {
      if (this._api) {
        this._api.sendTelemetry({
          ...payload,
          sessionId: this._sessionId,
        });
      }
    } catch { /* never throw */ }
  }
}

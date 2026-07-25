var __mercuryWidget__ = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // src/index.js
  var src_exports = {};
  __export(src_exports, {
    MercurySearch: () => MercurySearch
  });

  // src/styles.css
  var styles_default = `/**
 * Mercury Search Widget \u2013 Scoped Shadow DOM Styles
 *
 * All rules are scoped inside the Shadow Root.
 * - No global CSS injected
 * - No merchant styles can bleed in
 * - No Mercury styles can bleed out
 * - CSS variables for merchant customization
 * - box-sizing: border-box everywhere
 * - prefers-reduced-motion support
 * - WCAG AA contrast (4.5:1+ for text)
 * - Touch-friendly targets (min 44px)
 * - Viewport-aware dropdown
 */

/* ================================================================
   HOST \u2013 CSS variable contract (merchant customization API)
   ================================================================ */
:host {
  /* Merchant-facing CSS variables */
  --mercury-accent:  #5b5ef7;      /* Primary accent color          */
  --mercury-bg:      #ffffff;      /* Widget background             */
  --mercury-text:    #111827;      /* Primary text                  */
  --mercury-text-muted: #6b7280;   /* Secondary text                */
  --mercury-border:  #e5e7eb;      /* Border color                  */
  --mercury-hover:   #f9fafb;      /* Hover/selected background     */
  --mercury-error:   #dc2626;      /* Error state color             */
  --mercury-success: #16a34a;      /* In-stock indicator            */
  --mercury-font:    system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
  --mercury-radius:  8px;          /* Border radius                 */
  --mercury-shadow:  0 10px 40px -8px rgba(0, 0, 0, 0.15);

  /* Internal layout */
  display: block;
  box-sizing: border-box;
  font-family: var(--mercury-font);
  font-size: 16px;         /* Prevent iOS zoom on input focus */
  line-height: 1.5;
  color: var(--mercury-text);
}

/* Dark theme auto-detection */
@media (prefers-color-scheme: dark) {
  :host(:not([data-theme="light"])) {
    --mercury-bg:         #1e2435;
    --mercury-text:       #f0f2f8;
    --mercury-text-muted: #9aa5b4;
    --mercury-border:     #2d3748;
    --mercury-hover:      #252d3d;
  }
}

/* ================================================================
   Global reset \u2013 scoped inside shadow, does not affect merchant page
   ================================================================ */
*, *::before, *::after {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

/* ================================================================
   Wrapper
   ================================================================ */
.mw-wrapper {
  position: relative;
  width: 100%;
  font-family: var(--mercury-font);
  /* Reserve height to prevent layout shift */
  min-height: 48px;
}

/* ================================================================
   Input row
   ================================================================ */
.mw-input-row {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

/* Visually-hidden label (accessible but invisible) */
.mw-label {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}

/* Search icon */
.mw-search-icon {
  position: absolute;
  left: 14px;
  width: 18px;
  height: 18px;
  color: var(--mercury-text-muted);
  pointer-events: none;
  flex-shrink: 0;
}

/* Input */
.mw-input {
  width: 100%;
  height: 48px;          /* Fixed height \u2192 no layout shift */
  padding: 0 44px 0 44px;
  font-size: 16px;       /* Prevent iOS zoom */
  font-family: inherit;
  color: var(--mercury-text);
  background: var(--mercury-bg);
  border: 1.5px solid var(--mercury-border);
  border-radius: var(--mercury-radius);
  outline: none;
  appearance: none;
  -webkit-appearance: none;
  transition: border-color 0.18s ease, box-shadow 0.18s ease;
}

/* Remove browser default search cancel button */
.mw-input::-webkit-search-cancel-button,
.mw-input::-webkit-search-decoration {
  -webkit-appearance: none;
}

.mw-input:focus {
  border-color: var(--mercury-accent);
  box-shadow: 0 0 0 3px rgba(91, 94, 247, 0.15);
}

/* Focus visible ring \u2013 high contrast */
.mw-input:focus-visible {
  outline: 3px solid var(--mercury-accent);
  outline-offset: 2px;
}

/* Clear button */
.mw-clear-btn {
  position: absolute;
  right: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  min-width: 28px;
  padding: 0;
  background: none;
  border: none;
  border-radius: 50%;
  color: var(--mercury-text-muted);
  cursor: pointer;
  transition: background 0.15s ease, color 0.15s ease;
  /* Touch target extension */
  touch-action: manipulation;
}

.mw-clear-btn:hover {
  background: var(--mercury-hover);
  color: var(--mercury-text);
}

.mw-clear-btn:focus-visible {
  outline: 2px solid var(--mercury-accent);
  outline-offset: 1px;
}

.mw-clear-btn svg {
  width: 14px;
  height: 14px;
}

.mw-hidden {
  display: none !important;
}

/* ================================================================
   ARIA live status (visually hidden when empty)
   ================================================================ */
.mw-status {
  position: absolute;
  width: 1px;
  height: 1px;
  overflow: hidden;
  clip: rect(0 0 0 0);
  white-space: nowrap;
  pointer-events: none;
}

/* ================================================================
   Dropdown
   ================================================================ */
.mw-dropdown {
  position: absolute;
  top: calc(100% + 6px);
  left: 0;
  right: 0;
  z-index: 2147483647;    /* Max z-index \u2013 always above merchant content */
  background: var(--mercury-bg);
  border: 1px solid var(--mercury-border);
  border-radius: var(--mercury-radius);
  box-shadow: var(--mercury-shadow);
  max-height: 400px;
  overflow-y: auto;
  overflow-x: hidden;
  overscroll-behavior: contain;  /* Prevent body scroll on mobile */
  -webkit-overflow-scrolling: touch;
  display: none;
  opacity: 0;
}

/* Dropdown above input (viewport flip) */
.mw-dropdown.mw-flip {
  top: auto;
  bottom: calc(100% + 6px);
}

/* Open state */
.mw-dropdown.mw-open {
  display: block;
  opacity: 1;
}

/* Animation (respects prefers-reduced-motion) */
@media (prefers-reduced-motion: no-preference) {
  .mw-dropdown {
    transition: opacity 0.15s ease, transform 0.15s ease;
    transform: translateY(-4px);
  }
  .mw-dropdown.mw-open {
    transform: translateY(0);
  }
  .mw-dropdown.mw-flip {
    transform: translateY(4px);
  }
  .mw-dropdown.mw-flip.mw-open {
    transform: translateY(0);
  }
}

/* ================================================================
   State messages (loading / empty / error)
   ================================================================ */
.mw-state-msg {
  padding: 20px 16px;
  text-align: center;
  color: var(--mercury-text-muted);
  font-size: 14px;
  line-height: 1.5;
}

.mw-state-error {
  color: var(--mercury-error);
}

.mw-empty-hint {
  margin-top: 8px;
  font-size: 13px;
  color: var(--mercury-text-muted);
}

/* Spinner */
.mw-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid var(--mercury-border);
  border-top-color: var(--mercury-accent);
  border-radius: 50%;
  vertical-align: middle;
  margin-right: 8px;
}

@media (prefers-reduced-motion: no-preference) {
  .mw-spinner {
    animation: mw-spin 0.7s linear infinite;
  }
}

@keyframes mw-spin {
  to { transform: rotate(360deg); }
}

/* ================================================================
   Result items
   ================================================================ */
.mw-result-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  cursor: pointer;
  border-bottom: 1px solid var(--mercury-border);
  transition: background 0.12s ease;
  /* Minimum touch target */
  min-height: 56px;
  text-decoration: none;
  color: inherit;
}

.mw-result-item:last-child {
  border-bottom: none;
}

.mw-result-item:hover,
.mw-result-item.mw-selected {
  background: var(--mercury-hover);
}

.mw-result-item:focus-visible {
  outline: 2px solid var(--mercury-accent);
  outline-offset: -2px;
}

/* Image wrapper \u2013 fixed dimensions prevent layout shift */
.mw-img-wrap {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 6px;
  overflow: hidden;
  background: var(--mercury-hover);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mw-img {
  width: 48px;
  height: 48px;
  object-fit: cover;
  display: block;
}

.mw-img-placeholder {
  font-size: 22px;
  line-height: 1;
  color: var(--mercury-text-muted);
  user-select: none;
}

/* Content area */
.mw-result-content {
  flex: 1;
  min-width: 0;         /* Allow text truncation */
  overflow: hidden;
}

.mw-result-title {
  font-size: 14px;
  font-weight: 500;
  color: var(--mercury-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.mw-result-meta {
  font-size: 12px;
  color: var(--mercury-text-muted);
  margin-top: 2px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* Price + availability */
.mw-result-right {
  flex-shrink: 0;
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.mw-result-price {
  font-size: 14px;
  font-weight: 600;
  color: var(--mercury-text);
  white-space: nowrap;
}

.mw-result-avail {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: 20px;
  white-space: nowrap;
}

/* Color is NOT the only indicator (text also distinguishes) */
.mw-instock {
  background: rgba(22, 163, 74, 0.1);
  color: #15803d;
}

.mw-outstock {
  background: rgba(220, 38, 38, 0.1);
  color: #b91c1c;
}

/* Dark theme overrides for availability badges */
@media (prefers-color-scheme: dark) {
  :host(:not([data-theme="light"])) .mw-instock {
    color: #4ade80;
  }
  :host(:not([data-theme="light"])) .mw-outstock {
    color: #f87171;
  }
}

/* ================================================================
   Mobile-specific adjustments
   ================================================================ */
@media (max-width: 480px) {
  .mw-result-item {
    padding: 10px 12px;
    gap: 10px;
  }

  .mw-result-right {
    display: none;   /* Hide price on very small screens; title is more important */
  }

  .mw-dropdown {
    max-height: 60vh;
    border-radius: 0 0 var(--mercury-radius) var(--mercury-radius);
  }

  .mw-result-item {
    min-height: 60px;  /* Larger touch target on mobile */
  }
}

/* ================================================================
   High-contrast mode
   ================================================================ */
@media (forced-colors: active) {
  .mw-input {
    border: 2px solid ButtonText;
  }
  .mw-input:focus {
    outline: 3px solid Highlight;
  }
  .mw-result-item.mw-selected {
    background: Highlight;
    color: HighlightText;
  }
}
`;

  // src/api.js
  var REQUEST_TIMEOUT_MS = 8e3;
  var ApiErrorType = {
    ABORT: "abort",
    TIMEOUT: "timeout",
    RATE_LIMIT: "rate_limit",
    AUTH: "auth",
    NOT_FOUND: "not_found",
    SERVER: "server",
    NETWORK: "network"
  };
  var MercuryApiError = class extends Error {
    constructor(type, message) {
      super(message);
      this.type = type;
      this.name = "MercuryApiError";
    }
  };
  function isSafeUrl(url) {
    if (!url || typeof url !== "string")
      return false;
    try {
      const parsed = new URL(url);
      return parsed.protocol === "https:" || parsed.protocol === "http:";
    } catch (e) {
      return false;
    }
  }
  function getSessionId() {
    try {
      const key = "__msid";
      let id = sessionStorage.getItem(key);
      if (!id) {
        id = "ms_" + Math.random().toString(36).slice(2) + Date.now().toString(36);
        sessionStorage.setItem(key, id);
      }
      return id;
    } catch (e) {
      return "ms_" + Math.random().toString(36).slice(2);
    }
  }
  var SearchAPI = class {
    /**
     * @param {string} endpoint - Base URL (trailing slash stripped)
     * @param {string} apiKey   - Public pk_* key only
     */
    constructor(endpoint, apiKey) {
      this.endpoint = (endpoint || window.location.origin).replace(/\/$/, "");
      this.apiKey = apiKey;
      this._activeController = null;
    }
    /**
     * Execute a product search. Cancels any in-flight search first.
     * @param {string} query
     * @param {number} limit
     * @returns {Promise<{results: Array, searchId: string|null}>}
     */
    async search(query, limit = 8) {
      if (this._activeController) {
        this._activeController.abort();
      }
      const controller = new AbortController();
      this._activeController = controller;
      const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);
      try {
        const url = new URL("/api/v1/widget/search/instant", this.endpoint);
        url.searchParams.set("q", query);
        url.searchParams.set("limit", String(Math.min(limit, 50)));
        const response = await fetch(url.toString(), {
          method: "GET",
          headers: {
            "X-API-Key": this.apiKey,
            "Accept": "application/json"
          },
          signal: controller.signal
        });
        clearTimeout(timer);
        this._activeController = null;
        return await this._handleSearchResponse(response);
      } catch (err) {
        clearTimeout(timer);
        this._activeController = null;
        if (err.name === "AbortError") {
          throw new MercuryApiError(ApiErrorType.ABORT, "Request cancelled");
        }
        throw new MercuryApiError(ApiErrorType.NETWORK, "Network error. Please check your connection.");
      }
    }
    async _handleSearchResponse(response) {
      if (response.status === 429) {
        throw new MercuryApiError(ApiErrorType.RATE_LIMIT, "Too many requests. Please wait a moment and try again.");
      }
      if (response.status === 401 || response.status === 403) {
        throw new MercuryApiError(ApiErrorType.AUTH, "Search unavailable. Please contact the store owner.");
      }
      if (response.status === 404) {
        throw new MercuryApiError(ApiErrorType.NOT_FOUND, "Search service not found.");
      }
      if (!response.ok) {
        throw new MercuryApiError(ApiErrorType.SERVER, "Search is temporarily unavailable. Please try again.");
      }
      let data;
      try {
        data = await response.json();
      } catch (e) {
        throw new MercuryApiError(ApiErrorType.SERVER, "Unexpected response from server.");
      }
      const raw = Array.isArray(data.suggestions) ? data.suggestions : [];
      const results = raw.map((item) => this._sanitizeProduct(item));
      return {
        results,
        searchId: data.search_id && typeof data.search_id === "string" ? data.search_id : null
      };
    }
    /**
     * Return a safe product object with only whitelisted fields.
     * All string values go through the safe text path.
     */
    _sanitizeProduct(item) {
      if (!item || typeof item !== "object")
        return null;
      const title = typeof item.title === "string" ? item.title.trim() : "";
      const brand = typeof item.brand === "string" ? item.brand.trim() : "";
      const category = typeof item.category === "string" ? item.category.trim() : "";
      const price = typeof item.price === "number" ? item.price : typeof item.selling_price === "number" ? item.selling_price : null;
      const inStock = typeof item.in_stock === "boolean" ? item.in_stock : item.stock === true || item.stock === 1;
      const rawImage = item.image_url || item.image || "";
      const imageUrl = isSafeUrl(rawImage) ? rawImage : "";
      const rawUrl = item.url || item.product_url || "";
      const productUrl = isSafeUrl(rawUrl) ? rawUrl : "";
      const id = typeof item.id === "string" ? item.id : typeof item.id === "number" ? String(item.id) : "";
      return { id, title, brand, category, price, inStock, imageUrl, productUrl };
    }
    /**
     * Cancel any pending search request.
     */
    cancelSearch() {
      if (this._activeController) {
        this._activeController.abort();
        this._activeController = null;
      }
    }
    /**
     * Get widget config from the backend.
     * Non-blocking: failures return defaults.
     */
    async getWidgetConfig() {
      try {
        const url = new URL("/api/v1/widget/config", this.endpoint);
        const controller = new AbortController();
        const timer = setTimeout(() => controller.abort(), 5e3);
        const response = await fetch(url.toString(), {
          headers: { "X-API-Key": this.apiKey, "Accept": "application/json" },
          signal: controller.signal
        });
        clearTimeout(timer);
        if (!response.ok)
          return null;
        const data = await response.json();
        return data.success ? data.config : null;
      } catch (e) {
        return null;
      }
    }
    /**
     * Fire a telemetry event.
     * Never blocks navigation; uses sendBeacon when available.
     * @param {object} event - safe event payload
     */
    sendTelemetry(event) {
      try {
        const url = new URL("/api/v1/telemetry/events", this.endpoint).toString();
        const body = JSON.stringify({
          event_type: event.event || "unknown",
          product_id: event.productId || null,
          query: event.query || null,
          search_id: event.searchId || null,
          user_id: event.sessionId || null,
          metadata: {
            position: event.position || null,
            timestamp: (/* @__PURE__ */ new Date()).toISOString()
          }
        });
        if (navigator.sendBeacon) {
          const blob = new Blob([body], { type: "application/json" });
          const beaconUrl = url + "?k=" + encodeURIComponent(this.apiKey);
          const sent = navigator.sendBeacon(beaconUrl, blob);
          if (sent)
            return;
        }
        fetch(url, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": this.apiKey
          },
          body,
          keepalive: true
        }).catch(() => {
        });
      } catch (e) {
      }
    }
  };

  // src/ui.js
  function setText(el, text) {
    el.textContent = typeof text === "string" ? text : String(text != null ? text : "");
  }
  function createEl(tag, attrs = {}, textContent) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs)) {
      if (k === "className")
        el.className = v;
      else if (k === "role" || k === "aria-label" || k === "aria-expanded" || k === "aria-activedescendant" || k === "aria-controls" || k === "aria-selected" || k === "aria-live" || k === "aria-atomic" || k === "aria-busy" || k === "aria-haspopup" || k === "aria-autocomplete") {
        el.setAttribute(k, v);
      } else {
        el[k] = v;
      }
    }
    if (textContent !== void 0)
      setText(el, textContent);
    return el;
  }
  function debounce(fn, wait) {
    let t;
    return function(...args) {
      clearTimeout(t);
      t = setTimeout(() => fn.apply(this, args), wait);
    };
  }
  var MercurySearchElement = class extends HTMLElement {
    constructor() {
      super();
      this._shadow = this.attachShadow({ mode: "open" });
      this._api = null;
      this._config = null;
      this._state = {
        query: "",
        results: [],
        selectedIndex: -1,
        isLoading: false,
        isOpen: false,
        error: null,
        // null | string (safe message)
        searchId: null
      };
      this._sessionId = getSessionId();
      this._listeners = [];
      this._timers = [];
      this._debounceSearch = null;
      this._lastClickedProductId = null;
      this._lastClickTs = 0;
      this._els = {};
    }
    // ------------------------------------------------------------------
    // Web Component lifecycle
    // ------------------------------------------------------------------
    connectedCallback() {
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
      if (this._config)
        return;
      this._config = config;
      this._api = new SearchAPI(config.endpoint, config.apiKey);
      this._debounceSearch = debounce(this._executeSearch.bind(this), config.debounce || 200);
      this._buildShadow();
      this._bindEvents();
      this._sendTelemetry({ event: "widget_loaded" });
      this._api.getWidgetConfig().then((cfg) => {
        if (cfg)
          this._applyRemoteTheme(cfg);
      });
    }
    destroy() {
      if (this._api)
        this._api.cancelSearch();
      for (const { target, type, fn, opts } of this._listeners) {
        target.removeEventListener(type, fn, opts);
      }
      this._listeners = [];
      for (const id of this._timers)
        clearTimeout(id);
      this._timers = [];
      this._shadow.innerHTML = "";
      this._els = {};
      this._config = null;
      this._api = null;
    }
    // ------------------------------------------------------------------
    // Shadow DOM construction
    // ------------------------------------------------------------------
    _buildShadow() {
      const shadow = this._shadow;
      shadow.innerHTML = "";
      const styleEl = document.createElement("style");
      styleEl.textContent = styles_default;
      shadow.appendChild(styleEl);
      const wrapper = createEl("div", { className: "mw-wrapper" });
      const inputRow = createEl("div", { className: "mw-input-row" });
      const label = createEl("label", {
        className: "mw-label",
        htmlFor: "mw-input"
      }, "Search products");
      const searchIcon = this._makeSearchIcon();
      const input = createEl("input", {
        id: "mw-input",
        type: "search",
        className: "mw-input",
        autocomplete: "off",
        autocorrect: "off",
        autocapitalize: "off",
        spellcheck: false,
        "role": "combobox",
        "aria-expanded": "false",
        "aria-haspopup": "listbox",
        "aria-autocomplete": "list",
        "aria-controls": "mw-listbox",
        "aria-activedescendant": ""
      });
      setText(input, "");
      input.placeholder = this._config.placeholder;
      input.setAttribute("enterkeyhint", "search");
      const clearBtn = createEl("button", {
        className: "mw-clear-btn mw-hidden",
        type: "button",
        "aria-label": "Clear search"
      });
      clearBtn.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6L6 18M6 6l12 12" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>';
      inputRow.appendChild(label);
      inputRow.appendChild(searchIcon);
      inputRow.appendChild(input);
      inputRow.appendChild(clearBtn);
      const status = createEl("div", {
        className: "mw-status",
        role: "status",
        "aria-live": "polite",
        "aria-atomic": "true"
      });
      const dropdown = createEl("div", {
        id: "mw-listbox",
        className: "mw-dropdown",
        role: "listbox",
        "aria-label": "Search results"
      });
      dropdown.setAttribute("aria-hidden", "true");
      wrapper.appendChild(inputRow);
      wrapper.appendChild(status);
      wrapper.appendChild(dropdown);
      shadow.appendChild(wrapper);
      this._els = { input, clearBtn, status, dropdown, wrapper };
    }
    _makeSearchIcon() {
      const icon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      icon.setAttribute("class", "mw-search-icon");
      icon.setAttribute("viewBox", "0 0 24 24");
      icon.setAttribute("aria-hidden", "true");
      icon.setAttribute("focusable", "false");
      const path = document.createElementNS("http://www.w3.org/2000/svg", "path");
      path.setAttribute("d", "M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z");
      path.setAttribute("stroke", "currentColor");
      path.setAttribute("stroke-width", "2");
      path.setAttribute("stroke-linecap", "round");
      path.setAttribute("fill", "none");
      icon.appendChild(path);
      return icon;
    }
    // ------------------------------------------------------------------
    // Remote theme
    // ------------------------------------------------------------------
    _applyRemoteTheme(cfg) {
      const overrides = [];
      const safeColor = (v) => typeof v === "string" && /^#[0-9a-fA-F]{3,8}$|^rgba?\(|^hsl/.test(v) ? v : null;
      const safeFontFamily = (v) => typeof v === "string" && v.length < 200 ? v : null;
      const c = safeColor(cfg.widget_primary_color);
      if (c)
        overrides.push(`--mercury-accent: ${c};`);
      const f = safeFontFamily(cfg.widget_font_family);
      if (f)
        overrides.push(`--mercury-font: ${f}, system-ui, sans-serif;`);
      const ph = typeof cfg.widget_placeholder === "string" ? cfg.widget_placeholder : null;
      if (ph && this._els.input)
        this._els.input.placeholder = ph.slice(0, 100);
      if (overrides.length) {
        const extra = document.createElement("style");
        extra.textContent = `:host { ${overrides.join(" ")} }`;
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
      this._on(input, "input", () => {
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
      this._on(input, "keydown", (e) => this._handleKeydown(e));
      this._on(input, "focus", () => {
        if (this._state.query.trim().length >= (this._config.minLength || 2) && this._state.results.length) {
          this._openDropdown();
        }
      });
      this._on(clearBtn, "click", () => {
        input.value = "";
        this._state.query = "";
        this._state.results = [];
        this._state.selectedIndex = -1;
        this._closeDropdown();
        this._clearStatus();
        this._updateClearBtn();
        input.focus();
      });
      const outsideClick = (e) => {
        if (!this.contains(e.target) && !this._shadow.contains(e.target)) {
          this._closeDropdown();
        }
      };
      this._on(document, "click", outsideClick, true);
      const globalEsc = (e) => {
        if (e.key === "Escape" && this._state.isOpen) {
          this._closeDropdown();
          input.focus();
        }
      };
      this._on(document, "keydown", globalEsc, true);
      this._on(dropdown, "click", (e) => {
        const item = e.target.closest('[role="option"]');
        if (item) {
          const idx = parseInt(item.dataset.index, 10);
          if (Number.isFinite(idx))
            this._selectResult(idx);
        }
      });
      this._on(dropdown, "mousedown", (e) => {
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
        case "ArrowDown":
          if (!isOpen && count) {
            this._openDropdown();
            return;
          }
          if (!count)
            return;
          e.preventDefault();
          this._setSelected(selectedIndex < count - 1 ? selectedIndex + 1 : 0);
          break;
        case "ArrowUp":
          if (!isOpen || !count)
            return;
          e.preventDefault();
          this._setSelected(selectedIndex > 0 ? selectedIndex - 1 : count - 1);
          break;
        case "Enter":
          e.preventDefault();
          if (isOpen && selectedIndex >= 0 && selectedIndex < count) {
            this._selectResult(selectedIndex);
          } else if (this._state.query.trim().length >= (this._config.minLength || 2)) {
            this._executeSearch(this._state.query.trim());
          }
          break;
        case "Tab":
          if (isOpen)
            this._closeDropdown();
          break;
      }
    }
    _setSelected(idx) {
      this._state.selectedIndex = idx;
      this._updateSelectionDOM();
      const { input } = this._els;
      const itemId = idx >= 0 ? `mw-opt-${idx}` : "";
      input.setAttribute("aria-activedescendant", itemId);
    }
    _updateSelectionDOM() {
      const { dropdown } = this._els;
      const items = dropdown.querySelectorAll('[role="option"]');
      items.forEach((el, i) => {
        const selected = i === this._state.selectedIndex;
        el.setAttribute("aria-selected", selected ? "true" : "false");
        el.classList.toggle("mw-selected", selected);
        if (selected) {
          el.scrollIntoView({ block: "nearest", behavior: "smooth" });
        }
      });
    }
    // ------------------------------------------------------------------
    // Search execution
    // ------------------------------------------------------------------
    async _executeSearch(query) {
      if (!query || query.length < (this._config.minLength || 2))
        return;
      this._state.isLoading = true;
      this._state.error = null;
      this._state.selectedIndex = -1;
      this._renderLoading();
      this._openDropdown();
      this._announceStatus("Searching\u2026");
      this._sendTelemetry({ event: "search_requested", query });
      try {
        const { results, searchId } = await this._api.search(query, this._config.limit || 8);
        if (query !== this._state.query.trim())
          return;
        this._state.isLoading = false;
        this._state.results = results.filter(Boolean);
        this._state.searchId = searchId;
        this._renderResults();
        const count = this._state.results.length;
        if (count === 0) {
          this._announceStatus(`No results for "${query}"`);
          this._sendTelemetry({ event: "search_no_results", query });
        } else {
          this._announceStatus(`${count} result${count === 1 ? "" : "s"} found`);
          this._sendTelemetry({ event: "search_results_received", query, metadata: { count } });
        }
      } catch (err) {
        if (err instanceof MercuryApiError && err.type === ApiErrorType.ABORT)
          return;
        if (query !== this._state.query.trim())
          return;
        this._state.isLoading = false;
        this._state.error = err instanceof MercuryApiError ? err.message : "Search unavailable. Please try again.";
        this._renderError(this._state.error);
        this._announceStatus(this._state.error);
      }
    }
    // ------------------------------------------------------------------
    // Result selection
    // ------------------------------------------------------------------
    _selectResult(idx) {
      const item = this._state.results[idx];
      if (!item)
        return;
      const now = Date.now();
      if (this._lastClickedProductId === item.id && now - this._lastClickTs < 300)
        return;
      this._lastClickedProductId = item.id;
      this._lastClickTs = now;
      if (item.productUrl) {
        this._sendTelemetry({
          event: "search_result_clicked",
          query: this._state.query,
          productId: item.id,
          searchId: this._state.searchId,
          sessionId: this._sessionId,
          position: idx + 1
        });
        window.location.href = item.productUrl;
      } else {
        this._sendTelemetry({
          event: "search_result_clicked",
          query: this._state.query,
          productId: item.id,
          searchId: this._state.searchId,
          sessionId: this._sessionId,
          position: idx + 1
        });
        this.dispatchEvent(new CustomEvent("mercury:result-selected", {
          bubbles: true,
          composed: true,
          // crosses shadow boundary
          detail: { product: item, query: this._state.query, position: idx + 1 }
        }));
      }
      this._closeDropdown();
    }
    // ------------------------------------------------------------------
    // Dropdown open/close
    // ------------------------------------------------------------------
    _openDropdown() {
      if (this._state.isOpen)
        return;
      this._state.isOpen = true;
      const { dropdown, input } = this._els;
      dropdown.classList.add("mw-open");
      dropdown.setAttribute("aria-hidden", "false");
      input.setAttribute("aria-expanded", "true");
      this._positionDropdown();
    }
    _closeDropdown() {
      this._state.isOpen = false;
      this._state.selectedIndex = -1;
      const { dropdown, input } = this._els;
      dropdown.classList.remove("mw-open");
      dropdown.setAttribute("aria-hidden", "true");
      input.setAttribute("aria-expanded", "false");
      input.setAttribute("aria-activedescendant", "");
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
        dropdown.classList.add("mw-flip");
      } else {
        dropdown.classList.remove("mw-flip");
      }
    }
    // ------------------------------------------------------------------
    // Rendering helpers (all safe – no innerHTML with untrusted data)
    // ------------------------------------------------------------------
    _renderLoading() {
      const { dropdown } = this._els;
      dropdown.innerHTML = "";
      const msg = createEl("div", { className: "mw-state-msg", "aria-busy": "true" });
      const spinner = createEl("span", { className: "mw-spinner", "aria-hidden": "true" });
      msg.appendChild(spinner);
      msg.appendChild(document.createTextNode(" Searching\u2026"));
      dropdown.appendChild(msg);
      this._openDropdown();
    }
    _renderError(safeMsg) {
      const { dropdown } = this._els;
      dropdown.innerHTML = "";
      const msg = createEl("div", { className: "mw-state-msg mw-state-error" }, safeMsg);
      dropdown.appendChild(msg);
    }
    _renderResults() {
      const { dropdown } = this._els;
      const { results } = this._state;
      dropdown.innerHTML = "";
      if (results.length === 0) {
        const msg = createEl("div", { className: "mw-state-msg mw-state-empty" });
        setText(msg, 'No products found for "');
        const q = createEl("strong");
        setText(q, this._state.query);
        msg.appendChild(q);
        msg.appendChild(document.createTextNode('"'));
        const hint = createEl("p", { className: "mw-empty-hint" }, "Try different keywords or browse all categories.");
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
      const option = createEl("div", {
        className: "mw-result-item",
        role: "option",
        id: `mw-opt-${idx}`,
        "aria-selected": "false"
      });
      option.dataset.index = String(idx);
      const imgWrapper = createEl("div", { className: "mw-img-wrap" });
      if (item.imageUrl) {
        const img = createEl("img", {
          className: "mw-img",
          alt: item.title || "Product image",
          loading: "lazy",
          decoding: "async",
          width: "48",
          height: "48"
        });
        img.src = item.imageUrl;
        img.addEventListener("error", () => {
          imgWrapper.removeChild(img);
          const placeholder = createEl("div", { className: "mw-img-placeholder", "aria-hidden": "true" }, "\u{1F6CD}");
          imgWrapper.appendChild(placeholder);
        });
        imgWrapper.appendChild(img);
      } else {
        const placeholder = createEl("div", { className: "mw-img-placeholder", "aria-hidden": "true" }, "\u{1F6CD}");
        imgWrapper.appendChild(placeholder);
      }
      const content = createEl("div", { className: "mw-result-content" });
      const titleEl = createEl("div", { className: "mw-result-title" });
      setText(titleEl, item.title || "Unknown Product");
      const meta = createEl("div", { className: "mw-result-meta" });
      if (item.brand || item.category) {
        setText(meta, [item.brand, item.category].filter(Boolean).join(" \xB7 "));
      }
      content.appendChild(titleEl);
      if (item.brand || item.category)
        content.appendChild(meta);
      const right = createEl("div", { className: "mw-result-right" });
      if (item.price !== null && item.price !== void 0) {
        const price = createEl("div", { className: "mw-result-price" });
        setText(price, "$" + Number(item.price).toFixed(2));
        right.appendChild(price);
      }
      const avail = createEl("div", {
        className: "mw-result-avail " + (item.inStock ? "mw-instock" : "mw-outstock")
      });
      setText(avail, item.inStock ? "In stock" : "Out of stock");
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
      if (!status)
        return;
      setText(status, "");
      const t = setTimeout(() => setText(status, msg), 50);
      this._timers.push(t);
    }
    _clearStatus() {
      const { status } = this._els;
      if (status)
        setText(status, "");
    }
    // ------------------------------------------------------------------
    // Clear button visibility
    // ------------------------------------------------------------------
    _updateClearBtn() {
      const { clearBtn, input } = this._els;
      const hasText = input.value.length > 0;
      clearBtn.classList.toggle("mw-hidden", !hasText);
    }
    // ------------------------------------------------------------------
    // Telemetry (non-blocking, non-throwing)
    // ------------------------------------------------------------------
    _sendTelemetry(payload) {
      try {
        if (this._api) {
          this._api.sendTelemetry({
            ...payload,
            sessionId: this._sessionId
          });
        }
      } catch (e) {
      }
    }
  };

  // src/index.js
  if (!customElements.get("mercury-search")) {
    customElements.define("mercury-search", MercurySearchElement);
  }
  function parseConfig(script) {
    const raw = {
      apiKey: script.getAttribute("data-api-key") || "",
      endpoint: script.getAttribute("data-endpoint") || "",
      placeholder: script.getAttribute("data-placeholder") || "Search products\u2026",
      theme: script.getAttribute("data-theme") || "auto",
      limit: parseInt(script.getAttribute("data-limit") || "8", 10),
      minLength: parseInt(script.getAttribute("data-min-length") || "2", 10),
      debounce: parseInt(script.getAttribute("data-debounce") || "200", 10),
      target: script.getAttribute("data-target") || ""
    };
    const errors = [];
    if (!raw.apiKey) {
      errors.push("data-api-key is required");
    } else if (!raw.apiKey.startsWith("pk_")) {
      errors.push("data-api-key must be a public key starting with pk_");
    }
    if (raw.endpoint) {
      try {
        new URL(raw.endpoint);
      } catch (e) {
        errors.push("data-endpoint is not a valid URL");
      }
    }
    if (!Number.isFinite(raw.limit) || raw.limit < 1 || raw.limit > 50)
      raw.limit = 8;
    if (!Number.isFinite(raw.minLength) || raw.minLength < 1)
      raw.minLength = 2;
    if (!Number.isFinite(raw.debounce) || raw.debounce < 0)
      raw.debounce = 200;
    return { config: raw, errors };
  }
  function autoMount() {
    const scripts = document.querySelectorAll(
      'script[data-api-key], script[src*="mercury-widget"]'
    );
    let found = null;
    for (const s of scripts) {
      if (s.getAttribute("data-api-key")) {
        found = s;
        break;
      }
    }
    if (!found)
      return;
    const { config, errors } = parseConfig(found);
    if (errors.length) {
      if (typeof console !== "undefined") {
        console.warn("[MercurySearch] Configuration error(s):", errors.join("; "));
      }
      return;
    }
    let targetEl = null;
    if (config.target) {
      targetEl = document.querySelector(config.target);
      if (!targetEl) {
        console.warn('[MercurySearch] data-target selector "' + config.target + '" not found; inserting after script tag.');
      }
    }
    if (!targetEl) {
      const el = document.createElement("mercury-search");
      found.parentNode.insertBefore(el, found.nextSibling);
      targetEl = el;
    }
    _mountOnElement(targetEl, config);
  }
  function _mountOnElement(el, config) {
    if (el._mercuryMounted)
      return;
    el._mercuryMounted = true;
    let host = el;
    if (el.tagName.toLowerCase() !== "mercury-search") {
      host = document.createElement("mercury-search");
      el.appendChild(host);
    }
    host._mercuryConfig = config;
    if (typeof host.configure === "function") {
      host.configure(config);
    }
  }
  var MercurySearch = {
    _instances: /* @__PURE__ */ new Map(),
    /**
     * Programmatic mount.
     * @param {object} options - { target, apiKey, endpoint, placeholder, theme, limit }
     * @returns {{ destroy: Function }}
     */
    mount(options = {}) {
      const errors = [];
      const config = {
        apiKey: options.apiKey || "",
        endpoint: options.endpoint || "",
        placeholder: options.placeholder || "Search products\u2026",
        theme: options.theme || "auto",
        limit: options.limit || 8,
        minLength: options.minLength || 2,
        debounce: options.debounce || 200
      };
      if (!config.apiKey)
        errors.push("apiKey is required");
      else if (!config.apiKey.startsWith("pk_"))
        errors.push("apiKey must start with pk_");
      if (errors.length) {
        console.warn("[MercurySearch] mount() error:", errors.join("; "));
        return { destroy: () => {
        } };
      }
      let targetEl = null;
      if (options.target) {
        targetEl = typeof options.target === "string" ? document.querySelector(options.target) : options.target;
      }
      if (!targetEl) {
        console.warn("[MercurySearch] mount() requires a valid target element or selector");
        return { destroy: () => {
        } };
      }
      if (targetEl._mercuryInstance) {
        targetEl._mercuryInstance.destroy();
      }
      const host = document.createElement("mercury-search");
      host._mercuryConfig = config;
      targetEl.appendChild(host);
      const instance = {
        destroy() {
          if (typeof host.destroy === "function")
            host.destroy();
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
      document.querySelectorAll("mercury-search").forEach((el) => {
        if (typeof el.destroy === "function")
          el.destroy();
        el.remove();
      });
    },
    version: "2.0.0"
  };
  if (typeof window !== "undefined") {
    window.MercurySearch = MercurySearch;
  }
  if (typeof document !== "undefined") {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", autoMount, { once: true });
    } else {
      autoMount();
    }
  }
  return __toCommonJS(src_exports);
})();
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsic3JjL2luZGV4LmpzIiwgInNyYy9zdHlsZXMuY3NzIiwgInNyYy9hcGkuanMiLCAic3JjL3VpLmpzIl0sCiAgInNvdXJjZXNDb250ZW50IjogWyIvKipcbiAqIE1lcmN1cnkgU2VhcmNoIFdpZGdldCBcdTIwMTMgRW50cnkgUG9pbnRcbiAqIFplcm8tZGVwZW5kZW5jeSwgU2hhZG93IERPTS1pc29sYXRlZCwgc2NyaXB0LXRhZy1pbnN0YWxsYWJsZSBzZWFyY2ggd2lkZ2V0LlxuICpcbiAqIEVtYmVkOlxuICogICA8c2NyaXB0IHNyYz1cIi93aWRnZXQvbWVyY3VyeS13aWRnZXQuanNcIlxuICogICAgICAgICAgIGRhdGEtYXBpLWtleT1cInBrX3h4eFwiXG4gKiAgICAgICAgICAgZGF0YS1lbmRwb2ludD1cImh0dHBzOi8vc3RvcmUuZXhhbXBsZVwiXG4gKiAgICAgICAgICAgZGVmZXI+XG4gKiAgIDwvc2NyaXB0PlxuICpcbiAqIE9yIHByb2dyYW1tYXRpY2FsbHk6XG4gKiAgIHdpbmRvdy5NZXJjdXJ5U2VhcmNoLm1vdW50KHsgdGFyZ2V0OiAnI215LXNlYXJjaCcsIGFwaUtleTogJ3BrX3h4eCcgfSk7XG4gKi9cblxuaW1wb3J0IHsgTWVyY3VyeVNlYXJjaEVsZW1lbnQgfSBmcm9tICcuL3VpLmpzJztcblxuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4vLyAxLiBSZWdpc3RlciB0aGUgV2ViIENvbXBvbmVudCAoaWRlbXBvdGVudClcbi8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuaWYgKCFjdXN0b21FbGVtZW50cy5nZXQoJ21lcmN1cnktc2VhcmNoJykpIHtcbiAgY3VzdG9tRWxlbWVudHMuZGVmaW5lKCdtZXJjdXJ5LXNlYXJjaCcsIE1lcmN1cnlTZWFyY2hFbGVtZW50KTtcbn1cblxuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4vLyAyLiBDb25maWcgcGFyc2luZyBcdTIwMTMgaGFyZGVuZWRcbi8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuZnVuY3Rpb24gcGFyc2VDb25maWcoc2NyaXB0KSB7XG4gIGNvbnN0IHJhdyA9IHtcbiAgICBhcGlLZXk6ICAgICAgc2NyaXB0LmdldEF0dHJpYnV0ZSgnZGF0YS1hcGkta2V5JykgICAgICB8fCAnJyxcbiAgICBlbmRwb2ludDogICAgc2NyaXB0LmdldEF0dHJpYnV0ZSgnZGF0YS1lbmRwb2ludCcpICAgICB8fCAnJyxcbiAgICBwbGFjZWhvbGRlcjogc2NyaXB0LmdldEF0dHJpYnV0ZSgnZGF0YS1wbGFjZWhvbGRlcicpICB8fCAnU2VhcmNoIHByb2R1Y3RzXHUyMDI2JyxcbiAgICB0aGVtZTogICAgICAgc2NyaXB0LmdldEF0dHJpYnV0ZSgnZGF0YS10aGVtZScpICAgICAgICB8fCAnYXV0bycsXG4gICAgbGltaXQ6ICAgICAgIHBhcnNlSW50KHNjcmlwdC5nZXRBdHRyaWJ1dGUoJ2RhdGEtbGltaXQnKSB8fCAnOCcsIDEwKSxcbiAgICBtaW5MZW5ndGg6ICAgcGFyc2VJbnQoc2NyaXB0LmdldEF0dHJpYnV0ZSgnZGF0YS1taW4tbGVuZ3RoJykgfHwgJzInLCAxMCksXG4gICAgZGVib3VuY2U6ICAgIHBhcnNlSW50KHNjcmlwdC5nZXRBdHRyaWJ1dGUoJ2RhdGEtZGVib3VuY2UnKSB8fCAnMjAwJywgMTApLFxuICAgIHRhcmdldDogICAgICBzY3JpcHQuZ2V0QXR0cmlidXRlKCdkYXRhLXRhcmdldCcpICAgICAgIHx8ICcnLFxuICB9O1xuXG4gIGNvbnN0IGVycm9ycyA9IFtdO1xuXG4gIGlmICghcmF3LmFwaUtleSkge1xuICAgIGVycm9ycy5wdXNoKCdkYXRhLWFwaS1rZXkgaXMgcmVxdWlyZWQnKTtcbiAgfSBlbHNlIGlmICghcmF3LmFwaUtleS5zdGFydHNXaXRoKCdwa18nKSkge1xuICAgIGVycm9ycy5wdXNoKCdkYXRhLWFwaS1rZXkgbXVzdCBiZSBhIHB1YmxpYyBrZXkgc3RhcnRpbmcgd2l0aCBwa18nKTtcbiAgfVxuXG4gIGlmIChyYXcuZW5kcG9pbnQpIHtcbiAgICB0cnkgeyBuZXcgVVJMKHJhdy5lbmRwb2ludCk7IH0gY2F0Y2ggeyBlcnJvcnMucHVzaCgnZGF0YS1lbmRwb2ludCBpcyBub3QgYSB2YWxpZCBVUkwnKTsgfVxuICB9XG5cbiAgaWYgKCFOdW1iZXIuaXNGaW5pdGUocmF3LmxpbWl0KSB8fCByYXcubGltaXQgPCAxIHx8IHJhdy5saW1pdCA+IDUwKSByYXcubGltaXQgPSA4O1xuICBpZiAoIU51bWJlci5pc0Zpbml0ZShyYXcubWluTGVuZ3RoKSB8fCByYXcubWluTGVuZ3RoIDwgMSkgcmF3Lm1pbkxlbmd0aCA9IDI7XG4gIGlmICghTnVtYmVyLmlzRmluaXRlKHJhdy5kZWJvdW5jZSkgfHwgcmF3LmRlYm91bmNlIDwgMCkgcmF3LmRlYm91bmNlID0gMjAwO1xuXG4gIHJldHVybiB7IGNvbmZpZzogcmF3LCBlcnJvcnMgfTtcbn1cblxuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4vLyAzLiBTY3JpcHQtdGFnIGF1dG8tbW91bnRcbi8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuZnVuY3Rpb24gYXV0b01vdW50KCkge1xuICAvLyBGaW5kICp0aGlzKiBzY3JpcHQgdGFnIFx1MjAxMyB3b3JrcyB3aXRoIGRlZmVyLCB0eXBlPW1vZHVsZSwgYW5kIGNsYXNzaWMgc2NyaXB0LlxuICBjb25zdCBzY3JpcHRzID0gZG9jdW1lbnQucXVlcnlTZWxlY3RvckFsbChcbiAgICAnc2NyaXB0W2RhdGEtYXBpLWtleV0sIHNjcmlwdFtzcmMqPVwibWVyY3VyeS13aWRnZXRcIl0nXG4gICk7XG5cbiAgbGV0IGZvdW5kID0gbnVsbDtcbiAgZm9yIChjb25zdCBzIG9mIHNjcmlwdHMpIHtcbiAgICBpZiAocy5nZXRBdHRyaWJ1dGUoJ2RhdGEtYXBpLWtleScpKSB7IGZvdW5kID0gczsgYnJlYWs7IH1cbiAgfVxuICBpZiAoIWZvdW5kKSByZXR1cm47XG5cbiAgY29uc3QgeyBjb25maWcsIGVycm9ycyB9ID0gcGFyc2VDb25maWcoZm91bmQpO1xuXG4gIGlmIChlcnJvcnMubGVuZ3RoKSB7XG4gICAgaWYgKHR5cGVvZiBjb25zb2xlICE9PSAndW5kZWZpbmVkJykge1xuICAgICAgLy8gT25seSB3YXJuIGluIGRlYnVnL2RldjsgbmV2ZXIgdGhyb3cgdW5jYXVnaHQgZXJyb3JzLlxuICAgICAgY29uc29sZS53YXJuKCdbTWVyY3VyeVNlYXJjaF0gQ29uZmlndXJhdGlvbiBlcnJvcihzKTonLCBlcnJvcnMuam9pbignOyAnKSk7XG4gICAgfVxuICAgIHJldHVybjtcbiAgfVxuXG4gIC8vIERldGVybWluZSBtb3VudCB0YXJnZXRcbiAgbGV0IHRhcmdldEVsID0gbnVsbDtcbiAgaWYgKGNvbmZpZy50YXJnZXQpIHtcbiAgICB0YXJnZXRFbCA9IGRvY3VtZW50LnF1ZXJ5U2VsZWN0b3IoY29uZmlnLnRhcmdldCk7XG4gICAgaWYgKCF0YXJnZXRFbCkge1xuICAgICAgY29uc29sZS53YXJuKCdbTWVyY3VyeVNlYXJjaF0gZGF0YS10YXJnZXQgc2VsZWN0b3IgXCInICsgY29uZmlnLnRhcmdldCArICdcIiBub3QgZm91bmQ7IGluc2VydGluZyBhZnRlciBzY3JpcHQgdGFnLicpO1xuICAgIH1cbiAgfVxuXG4gIGlmICghdGFyZ2V0RWwpIHtcbiAgICAvLyBJbnNlcnQgYSA8bWVyY3VyeS1zZWFyY2g+IGVsZW1lbnQgcmlnaHQgYWZ0ZXIgdGhpcyBzY3JpcHQgdGFnXG4gICAgY29uc3QgZWwgPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KCdtZXJjdXJ5LXNlYXJjaCcpO1xuICAgIGZvdW5kLnBhcmVudE5vZGUuaW5zZXJ0QmVmb3JlKGVsLCBmb3VuZC5uZXh0U2libGluZyk7XG4gICAgdGFyZ2V0RWwgPSBlbDtcbiAgfVxuXG4gIF9tb3VudE9uRWxlbWVudCh0YXJnZXRFbCwgY29uZmlnKTtcbn1cblxuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4vLyA0LiBfbW91bnRPbkVsZW1lbnQgXHUyMDEzIHNoYXJlZCBsb2dpY1xuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG5mdW5jdGlvbiBfbW91bnRPbkVsZW1lbnQoZWwsIGNvbmZpZykge1xuICAvLyBJZGVtcG90ZW5jeTogc2tpcCBpZiBhbHJlYWR5IG1vdW50ZWRcbiAgaWYgKGVsLl9tZXJjdXJ5TW91bnRlZCkgcmV0dXJuO1xuICBlbC5fbWVyY3VyeU1vdW50ZWQgPSB0cnVlO1xuXG4gIC8vIElmIGVsZW1lbnQgaXMgbm90IG1lcmN1cnktc2VhcmNoLCB3cmFwIGl0XG4gIGxldCBob3N0ID0gZWw7XG4gIGlmIChlbC50YWdOYW1lLnRvTG93ZXJDYXNlKCkgIT09ICdtZXJjdXJ5LXNlYXJjaCcpIHtcbiAgICBob3N0ID0gZG9jdW1lbnQuY3JlYXRlRWxlbWVudCgnbWVyY3VyeS1zZWFyY2gnKTtcbiAgICBlbC5hcHBlbmRDaGlsZChob3N0KTtcbiAgfVxuXG4gIC8vIFBhc3MgY29uZmlnIGludG8gdGhlIGN1c3RvbSBlbGVtZW50XG4gIGhvc3QuX21lcmN1cnlDb25maWcgPSBjb25maWc7XG4gIC8vIElmIGFscmVhZHkgdXBncmFkZWQgKGFscmVhZHkgaW4gRE9NKSwgY2FsbCBjb25maWd1cmVcbiAgaWYgKHR5cGVvZiBob3N0LmNvbmZpZ3VyZSA9PT0gJ2Z1bmN0aW9uJykge1xuICAgIGhvc3QuY29uZmlndXJlKGNvbmZpZyk7XG4gIH1cbiAgLy8gZWxzZTogY29ubmVjdGVkQ2FsbGJhY2sgd2lsbCBjYWxsIGNvbmZpZ3VyZSB2aWEgX21lcmN1cnlDb25maWdcbn1cblxuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4vLyA1LiBQdWJsaWMgQVBJOiB3aW5kb3cuTWVyY3VyeVNlYXJjaFxuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG5jb25zdCBNZXJjdXJ5U2VhcmNoID0ge1xuICBfaW5zdGFuY2VzOiBuZXcgTWFwKCksXG5cbiAgLyoqXG4gICAqIFByb2dyYW1tYXRpYyBtb3VudC5cbiAgICogQHBhcmFtIHtvYmplY3R9IG9wdGlvbnMgLSB7IHRhcmdldCwgYXBpS2V5LCBlbmRwb2ludCwgcGxhY2Vob2xkZXIsIHRoZW1lLCBsaW1pdCB9XG4gICAqIEByZXR1cm5zIHt7IGRlc3Ryb3k6IEZ1bmN0aW9uIH19XG4gICAqL1xuICBtb3VudChvcHRpb25zID0ge30pIHtcbiAgICBjb25zdCBlcnJvcnMgPSBbXTtcbiAgICBjb25zdCBjb25maWcgPSB7XG4gICAgICBhcGlLZXk6ICAgICAgb3B0aW9ucy5hcGlLZXkgICAgICB8fCAnJyxcbiAgICAgIGVuZHBvaW50OiAgICBvcHRpb25zLmVuZHBvaW50ICAgIHx8ICcnLFxuICAgICAgcGxhY2Vob2xkZXI6IG9wdGlvbnMucGxhY2Vob2xkZXIgfHwgJ1NlYXJjaCBwcm9kdWN0c1x1MjAyNicsXG4gICAgICB0aGVtZTogICAgICAgb3B0aW9ucy50aGVtZSAgICAgICB8fCAnYXV0bycsXG4gICAgICBsaW1pdDogICAgICAgb3B0aW9ucy5saW1pdCAgICAgICB8fCA4LFxuICAgICAgbWluTGVuZ3RoOiAgIG9wdGlvbnMubWluTGVuZ3RoICAgfHwgMixcbiAgICAgIGRlYm91bmNlOiAgICBvcHRpb25zLmRlYm91bmNlICAgIHx8IDIwMCxcbiAgICB9O1xuXG4gICAgaWYgKCFjb25maWcuYXBpS2V5KSBlcnJvcnMucHVzaCgnYXBpS2V5IGlzIHJlcXVpcmVkJyk7XG4gICAgZWxzZSBpZiAoIWNvbmZpZy5hcGlLZXkuc3RhcnRzV2l0aCgncGtfJykpIGVycm9ycy5wdXNoKCdhcGlLZXkgbXVzdCBzdGFydCB3aXRoIHBrXycpO1xuXG4gICAgaWYgKGVycm9ycy5sZW5ndGgpIHtcbiAgICAgIGNvbnNvbGUud2FybignW01lcmN1cnlTZWFyY2hdIG1vdW50KCkgZXJyb3I6JywgZXJyb3JzLmpvaW4oJzsgJykpO1xuICAgICAgcmV0dXJuIHsgZGVzdHJveTogKCkgPT4ge30gfTtcbiAgICB9XG5cbiAgICBsZXQgdGFyZ2V0RWwgPSBudWxsO1xuICAgIGlmIChvcHRpb25zLnRhcmdldCkge1xuICAgICAgdGFyZ2V0RWwgPSB0eXBlb2Ygb3B0aW9ucy50YXJnZXQgPT09ICdzdHJpbmcnXG4gICAgICAgID8gZG9jdW1lbnQucXVlcnlTZWxlY3RvcihvcHRpb25zLnRhcmdldClcbiAgICAgICAgOiBvcHRpb25zLnRhcmdldDtcbiAgICB9XG5cbiAgICBpZiAoIXRhcmdldEVsKSB7XG4gICAgICBjb25zb2xlLndhcm4oJ1tNZXJjdXJ5U2VhcmNoXSBtb3VudCgpIHJlcXVpcmVzIGEgdmFsaWQgdGFyZ2V0IGVsZW1lbnQgb3Igc2VsZWN0b3InKTtcbiAgICAgIHJldHVybiB7IGRlc3Ryb3k6ICgpID0+IHt9IH07XG4gICAgfVxuXG4gICAgLy8gSWRlbXBvdGVuY3k6IGlmIGFscmVhZHkgbW91bnRlZCBvbiB0aGlzIGVsZW1lbnQsIGRlc3Ryb3kgZmlyc3RcbiAgICBpZiAodGFyZ2V0RWwuX21lcmN1cnlJbnN0YW5jZSkge1xuICAgICAgdGFyZ2V0RWwuX21lcmN1cnlJbnN0YW5jZS5kZXN0cm95KCk7XG4gICAgfVxuXG4gICAgY29uc3QgaG9zdCA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ21lcmN1cnktc2VhcmNoJyk7XG4gICAgaG9zdC5fbWVyY3VyeUNvbmZpZyA9IGNvbmZpZztcbiAgICB0YXJnZXRFbC5hcHBlbmRDaGlsZChob3N0KTtcblxuICAgIGNvbnN0IGluc3RhbmNlID0ge1xuICAgICAgZGVzdHJveSgpIHtcbiAgICAgICAgaWYgKHR5cGVvZiBob3N0LmRlc3Ryb3kgPT09ICdmdW5jdGlvbicpIGhvc3QuZGVzdHJveSgpO1xuICAgICAgICBob3N0LnJlbW92ZSgpO1xuICAgICAgICB0YXJnZXRFbC5fbWVyY3VyeUluc3RhbmNlID0gbnVsbDtcbiAgICAgIH1cbiAgICB9O1xuXG4gICAgdGFyZ2V0RWwuX21lcmN1cnlJbnN0YW5jZSA9IGluc3RhbmNlO1xuICAgIHJldHVybiBpbnN0YW5jZTtcbiAgfSxcblxuICAvKipcbiAgICogRGVzdHJveSBhbGwgbW91bnRlZCB3aWRnZXRzLlxuICAgKi9cbiAgZGVzdHJveUFsbCgpIHtcbiAgICBkb2N1bWVudC5xdWVyeVNlbGVjdG9yQWxsKCdtZXJjdXJ5LXNlYXJjaCcpLmZvckVhY2goZWwgPT4ge1xuICAgICAgaWYgKHR5cGVvZiBlbC5kZXN0cm95ID09PSAnZnVuY3Rpb24nKSBlbC5kZXN0cm95KCk7XG4gICAgICBlbC5yZW1vdmUoKTtcbiAgICB9KTtcbiAgfSxcblxuICB2ZXJzaW9uOiAnMi4wLjAnLFxufTtcblxuLy8gRXhwb3NlIGdsb2JhbGx5IChvbmUgbmFtZSwgb25lIG5hbWVzcGFjZSlcbmlmICh0eXBlb2Ygd2luZG93ICE9PSAndW5kZWZpbmVkJykge1xuICB3aW5kb3cuTWVyY3VyeVNlYXJjaCA9IE1lcmN1cnlTZWFyY2g7XG59XG5cbi8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuLy8gNi4gQXV0by1pbml0aWFsaXplXG4vLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbmlmICh0eXBlb2YgZG9jdW1lbnQgIT09ICd1bmRlZmluZWQnKSB7XG4gIGlmIChkb2N1bWVudC5yZWFkeVN0YXRlID09PSAnbG9hZGluZycpIHtcbiAgICBkb2N1bWVudC5hZGRFdmVudExpc3RlbmVyKCdET01Db250ZW50TG9hZGVkJywgYXV0b01vdW50LCB7IG9uY2U6IHRydWUgfSk7XG4gIH0gZWxzZSB7XG4gICAgYXV0b01vdW50KCk7XG4gIH1cbn1cblxuZXhwb3J0IHsgTWVyY3VyeVNlYXJjaCB9O1xuIiwgIi8qKlxuICogTWVyY3VyeSBTZWFyY2ggV2lkZ2V0IFx1MjAxMyBTY29wZWQgU2hhZG93IERPTSBTdHlsZXNcbiAqXG4gKiBBbGwgcnVsZXMgYXJlIHNjb3BlZCBpbnNpZGUgdGhlIFNoYWRvdyBSb290LlxuICogLSBObyBnbG9iYWwgQ1NTIGluamVjdGVkXG4gKiAtIE5vIG1lcmNoYW50IHN0eWxlcyBjYW4gYmxlZWQgaW5cbiAqIC0gTm8gTWVyY3VyeSBzdHlsZXMgY2FuIGJsZWVkIG91dFxuICogLSBDU1MgdmFyaWFibGVzIGZvciBtZXJjaGFudCBjdXN0b21pemF0aW9uXG4gKiAtIGJveC1zaXppbmc6IGJvcmRlci1ib3ggZXZlcnl3aGVyZVxuICogLSBwcmVmZXJzLXJlZHVjZWQtbW90aW9uIHN1cHBvcnRcbiAqIC0gV0NBRyBBQSBjb250cmFzdCAoNC41OjErIGZvciB0ZXh0KVxuICogLSBUb3VjaC1mcmllbmRseSB0YXJnZXRzIChtaW4gNDRweClcbiAqIC0gVmlld3BvcnQtYXdhcmUgZHJvcGRvd25cbiAqL1xuXG4vKiA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG4gICBIT1NUIFx1MjAxMyBDU1MgdmFyaWFibGUgY29udHJhY3QgKG1lcmNoYW50IGN1c3RvbWl6YXRpb24gQVBJKVxuICAgPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PSAqL1xuOmhvc3Qge1xuICAvKiBNZXJjaGFudC1mYWNpbmcgQ1NTIHZhcmlhYmxlcyAqL1xuICAtLW1lcmN1cnktYWNjZW50OiAgIzViNWVmNzsgICAgICAvKiBQcmltYXJ5IGFjY2VudCBjb2xvciAgICAgICAgICAqL1xuICAtLW1lcmN1cnktYmc6ICAgICAgI2ZmZmZmZjsgICAgICAvKiBXaWRnZXQgYmFja2dyb3VuZCAgICAgICAgICAgICAqL1xuICAtLW1lcmN1cnktdGV4dDogICAgIzExMTgyNzsgICAgICAvKiBQcmltYXJ5IHRleHQgICAgICAgICAgICAgICAgICAqL1xuICAtLW1lcmN1cnktdGV4dC1tdXRlZDogIzZiNzI4MDsgICAvKiBTZWNvbmRhcnkgdGV4dCAgICAgICAgICAgICAgICAqL1xuICAtLW1lcmN1cnktYm9yZGVyOiAgI2U1ZTdlYjsgICAgICAvKiBCb3JkZXIgY29sb3IgICAgICAgICAgICAgICAgICAqL1xuICAtLW1lcmN1cnktaG92ZXI6ICAgI2Y5ZmFmYjsgICAgICAvKiBIb3Zlci9zZWxlY3RlZCBiYWNrZ3JvdW5kICAgICAqL1xuICAtLW1lcmN1cnktZXJyb3I6ICAgI2RjMjYyNjsgICAgICAvKiBFcnJvciBzdGF0ZSBjb2xvciAgICAgICAgICAgICAqL1xuICAtLW1lcmN1cnktc3VjY2VzczogIzE2YTM0YTsgICAgICAvKiBJbi1zdG9jayBpbmRpY2F0b3IgICAgICAgICAgICAqL1xuICAtLW1lcmN1cnktZm9udDogICAgc3lzdGVtLXVpLCAtYXBwbGUtc3lzdGVtLCAnU2Vnb2UgVUknLCBSb2JvdG8sIHNhbnMtc2VyaWY7XG4gIC0tbWVyY3VyeS1yYWRpdXM6ICA4cHg7ICAgICAgICAgIC8qIEJvcmRlciByYWRpdXMgICAgICAgICAgICAgICAgICovXG4gIC0tbWVyY3VyeS1zaGFkb3c6ICAwIDEwcHggNDBweCAtOHB4IHJnYmEoMCwgMCwgMCwgMC4xNSk7XG5cbiAgLyogSW50ZXJuYWwgbGF5b3V0ICovXG4gIGRpc3BsYXk6IGJsb2NrO1xuICBib3gtc2l6aW5nOiBib3JkZXItYm94O1xuICBmb250LWZhbWlseTogdmFyKC0tbWVyY3VyeS1mb250KTtcbiAgZm9udC1zaXplOiAxNnB4OyAgICAgICAgIC8qIFByZXZlbnQgaU9TIHpvb20gb24gaW5wdXQgZm9jdXMgKi9cbiAgbGluZS1oZWlnaHQ6IDEuNTtcbiAgY29sb3I6IHZhcigtLW1lcmN1cnktdGV4dCk7XG59XG5cbi8qIERhcmsgdGhlbWUgYXV0by1kZXRlY3Rpb24gKi9cbkBtZWRpYSAocHJlZmVycy1jb2xvci1zY2hlbWU6IGRhcmspIHtcbiAgOmhvc3QoOm5vdChbZGF0YS10aGVtZT1cImxpZ2h0XCJdKSkge1xuICAgIC0tbWVyY3VyeS1iZzogICAgICAgICAjMWUyNDM1O1xuICAgIC0tbWVyY3VyeS10ZXh0OiAgICAgICAjZjBmMmY4O1xuICAgIC0tbWVyY3VyeS10ZXh0LW11dGVkOiAjOWFhNWI0O1xuICAgIC0tbWVyY3VyeS1ib3JkZXI6ICAgICAjMmQzNzQ4O1xuICAgIC0tbWVyY3VyeS1ob3ZlcjogICAgICAjMjUyZDNkO1xuICB9XG59XG5cbi8qID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cbiAgIEdsb2JhbCByZXNldCBcdTIwMTMgc2NvcGVkIGluc2lkZSBzaGFkb3csIGRvZXMgbm90IGFmZmVjdCBtZXJjaGFudCBwYWdlXG4gICA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09ICovXG4qLCAqOjpiZWZvcmUsICo6OmFmdGVyIHtcbiAgYm94LXNpemluZzogYm9yZGVyLWJveDtcbiAgbWFyZ2luOiAwO1xuICBwYWRkaW5nOiAwO1xufVxuXG4vKiA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG4gICBXcmFwcGVyXG4gICA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09ICovXG4ubXctd3JhcHBlciB7XG4gIHBvc2l0aW9uOiByZWxhdGl2ZTtcbiAgd2lkdGg6IDEwMCU7XG4gIGZvbnQtZmFtaWx5OiB2YXIoLS1tZXJjdXJ5LWZvbnQpO1xuICAvKiBSZXNlcnZlIGhlaWdodCB0byBwcmV2ZW50IGxheW91dCBzaGlmdCAqL1xuICBtaW4taGVpZ2h0OiA0OHB4O1xufVxuXG4vKiA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG4gICBJbnB1dCByb3dcbiAgID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0gKi9cbi5tdy1pbnB1dC1yb3cge1xuICBwb3NpdGlvbjogcmVsYXRpdmU7XG4gIGRpc3BsYXk6IGZsZXg7XG4gIGFsaWduLWl0ZW1zOiBjZW50ZXI7XG4gIHdpZHRoOiAxMDAlO1xufVxuXG4vKiBWaXN1YWxseS1oaWRkZW4gbGFiZWwgKGFjY2Vzc2libGUgYnV0IGludmlzaWJsZSkgKi9cbi5tdy1sYWJlbCB7XG4gIHBvc2l0aW9uOiBhYnNvbHV0ZTtcbiAgd2lkdGg6IDFweDtcbiAgaGVpZ2h0OiAxcHg7XG4gIHBhZGRpbmc6IDA7XG4gIG1hcmdpbjogLTFweDtcbiAgb3ZlcmZsb3c6IGhpZGRlbjtcbiAgY2xpcDogcmVjdCgwLCAwLCAwLCAwKTtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbiAgYm9yZGVyOiAwO1xufVxuXG4vKiBTZWFyY2ggaWNvbiAqL1xuLm13LXNlYXJjaC1pY29uIHtcbiAgcG9zaXRpb246IGFic29sdXRlO1xuICBsZWZ0OiAxNHB4O1xuICB3aWR0aDogMThweDtcbiAgaGVpZ2h0OiAxOHB4O1xuICBjb2xvcjogdmFyKC0tbWVyY3VyeS10ZXh0LW11dGVkKTtcbiAgcG9pbnRlci1ldmVudHM6IG5vbmU7XG4gIGZsZXgtc2hyaW5rOiAwO1xufVxuXG4vKiBJbnB1dCAqL1xuLm13LWlucHV0IHtcbiAgd2lkdGg6IDEwMCU7XG4gIGhlaWdodDogNDhweDsgICAgICAgICAgLyogRml4ZWQgaGVpZ2h0IFx1MjE5MiBubyBsYXlvdXQgc2hpZnQgKi9cbiAgcGFkZGluZzogMCA0NHB4IDAgNDRweDtcbiAgZm9udC1zaXplOiAxNnB4OyAgICAgICAvKiBQcmV2ZW50IGlPUyB6b29tICovXG4gIGZvbnQtZmFtaWx5OiBpbmhlcml0O1xuICBjb2xvcjogdmFyKC0tbWVyY3VyeS10ZXh0KTtcbiAgYmFja2dyb3VuZDogdmFyKC0tbWVyY3VyeS1iZyk7XG4gIGJvcmRlcjogMS41cHggc29saWQgdmFyKC0tbWVyY3VyeS1ib3JkZXIpO1xuICBib3JkZXItcmFkaXVzOiB2YXIoLS1tZXJjdXJ5LXJhZGl1cyk7XG4gIG91dGxpbmU6IG5vbmU7XG4gIGFwcGVhcmFuY2U6IG5vbmU7XG4gIC13ZWJraXQtYXBwZWFyYW5jZTogbm9uZTtcbiAgdHJhbnNpdGlvbjogYm9yZGVyLWNvbG9yIDAuMThzIGVhc2UsIGJveC1zaGFkb3cgMC4xOHMgZWFzZTtcbn1cblxuLyogUmVtb3ZlIGJyb3dzZXIgZGVmYXVsdCBzZWFyY2ggY2FuY2VsIGJ1dHRvbiAqL1xuLm13LWlucHV0Ojotd2Via2l0LXNlYXJjaC1jYW5jZWwtYnV0dG9uLFxuLm13LWlucHV0Ojotd2Via2l0LXNlYXJjaC1kZWNvcmF0aW9uIHtcbiAgLXdlYmtpdC1hcHBlYXJhbmNlOiBub25lO1xufVxuXG4ubXctaW5wdXQ6Zm9jdXMge1xuICBib3JkZXItY29sb3I6IHZhcigtLW1lcmN1cnktYWNjZW50KTtcbiAgYm94LXNoYWRvdzogMCAwIDAgM3B4IHJnYmEoOTEsIDk0LCAyNDcsIDAuMTUpO1xufVxuXG4vKiBGb2N1cyB2aXNpYmxlIHJpbmcgXHUyMDEzIGhpZ2ggY29udHJhc3QgKi9cbi5tdy1pbnB1dDpmb2N1cy12aXNpYmxlIHtcbiAgb3V0bGluZTogM3B4IHNvbGlkIHZhcigtLW1lcmN1cnktYWNjZW50KTtcbiAgb3V0bGluZS1vZmZzZXQ6IDJweDtcbn1cblxuLyogQ2xlYXIgYnV0dG9uICovXG4ubXctY2xlYXItYnRuIHtcbiAgcG9zaXRpb246IGFic29sdXRlO1xuICByaWdodDogMTBweDtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7XG4gIHdpZHRoOiAyOHB4O1xuICBoZWlnaHQ6IDI4cHg7XG4gIG1pbi13aWR0aDogMjhweDtcbiAgcGFkZGluZzogMDtcbiAgYmFja2dyb3VuZDogbm9uZTtcbiAgYm9yZGVyOiBub25lO1xuICBib3JkZXItcmFkaXVzOiA1MCU7XG4gIGNvbG9yOiB2YXIoLS1tZXJjdXJ5LXRleHQtbXV0ZWQpO1xuICBjdXJzb3I6IHBvaW50ZXI7XG4gIHRyYW5zaXRpb246IGJhY2tncm91bmQgMC4xNXMgZWFzZSwgY29sb3IgMC4xNXMgZWFzZTtcbiAgLyogVG91Y2ggdGFyZ2V0IGV4dGVuc2lvbiAqL1xuICB0b3VjaC1hY3Rpb246IG1hbmlwdWxhdGlvbjtcbn1cblxuLm13LWNsZWFyLWJ0bjpob3ZlciB7XG4gIGJhY2tncm91bmQ6IHZhcigtLW1lcmN1cnktaG92ZXIpO1xuICBjb2xvcjogdmFyKC0tbWVyY3VyeS10ZXh0KTtcbn1cblxuLm13LWNsZWFyLWJ0bjpmb2N1cy12aXNpYmxlIHtcbiAgb3V0bGluZTogMnB4IHNvbGlkIHZhcigtLW1lcmN1cnktYWNjZW50KTtcbiAgb3V0bGluZS1vZmZzZXQ6IDFweDtcbn1cblxuLm13LWNsZWFyLWJ0biBzdmcge1xuICB3aWR0aDogMTRweDtcbiAgaGVpZ2h0OiAxNHB4O1xufVxuXG4ubXctaGlkZGVuIHtcbiAgZGlzcGxheTogbm9uZSAhaW1wb3J0YW50O1xufVxuXG4vKiA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG4gICBBUklBIGxpdmUgc3RhdHVzICh2aXN1YWxseSBoaWRkZW4gd2hlbiBlbXB0eSlcbiAgID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0gKi9cbi5tdy1zdGF0dXMge1xuICBwb3NpdGlvbjogYWJzb2x1dGU7XG4gIHdpZHRoOiAxcHg7XG4gIGhlaWdodDogMXB4O1xuICBvdmVyZmxvdzogaGlkZGVuO1xuICBjbGlwOiByZWN0KDAgMCAwIDApO1xuICB3aGl0ZS1zcGFjZTogbm93cmFwO1xuICBwb2ludGVyLWV2ZW50czogbm9uZTtcbn1cblxuLyogPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuICAgRHJvcGRvd25cbiAgID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT0gKi9cbi5tdy1kcm9wZG93biB7XG4gIHBvc2l0aW9uOiBhYnNvbHV0ZTtcbiAgdG9wOiBjYWxjKDEwMCUgKyA2cHgpO1xuICBsZWZ0OiAwO1xuICByaWdodDogMDtcbiAgei1pbmRleDogMjE0NzQ4MzY0NzsgICAgLyogTWF4IHotaW5kZXggXHUyMDEzIGFsd2F5cyBhYm92ZSBtZXJjaGFudCBjb250ZW50ICovXG4gIGJhY2tncm91bmQ6IHZhcigtLW1lcmN1cnktYmcpO1xuICBib3JkZXI6IDFweCBzb2xpZCB2YXIoLS1tZXJjdXJ5LWJvcmRlcik7XG4gIGJvcmRlci1yYWRpdXM6IHZhcigtLW1lcmN1cnktcmFkaXVzKTtcbiAgYm94LXNoYWRvdzogdmFyKC0tbWVyY3VyeS1zaGFkb3cpO1xuICBtYXgtaGVpZ2h0OiA0MDBweDtcbiAgb3ZlcmZsb3cteTogYXV0bztcbiAgb3ZlcmZsb3cteDogaGlkZGVuO1xuICBvdmVyc2Nyb2xsLWJlaGF2aW9yOiBjb250YWluOyAgLyogUHJldmVudCBib2R5IHNjcm9sbCBvbiBtb2JpbGUgKi9cbiAgLXdlYmtpdC1vdmVyZmxvdy1zY3JvbGxpbmc6IHRvdWNoO1xuICBkaXNwbGF5OiBub25lO1xuICBvcGFjaXR5OiAwO1xufVxuXG4vKiBEcm9wZG93biBhYm92ZSBpbnB1dCAodmlld3BvcnQgZmxpcCkgKi9cbi5tdy1kcm9wZG93bi5tdy1mbGlwIHtcbiAgdG9wOiBhdXRvO1xuICBib3R0b206IGNhbGMoMTAwJSArIDZweCk7XG59XG5cbi8qIE9wZW4gc3RhdGUgKi9cbi5tdy1kcm9wZG93bi5tdy1vcGVuIHtcbiAgZGlzcGxheTogYmxvY2s7XG4gIG9wYWNpdHk6IDE7XG59XG5cbi8qIEFuaW1hdGlvbiAocmVzcGVjdHMgcHJlZmVycy1yZWR1Y2VkLW1vdGlvbikgKi9cbkBtZWRpYSAocHJlZmVycy1yZWR1Y2VkLW1vdGlvbjogbm8tcHJlZmVyZW5jZSkge1xuICAubXctZHJvcGRvd24ge1xuICAgIHRyYW5zaXRpb246IG9wYWNpdHkgMC4xNXMgZWFzZSwgdHJhbnNmb3JtIDAuMTVzIGVhc2U7XG4gICAgdHJhbnNmb3JtOiB0cmFuc2xhdGVZKC00cHgpO1xuICB9XG4gIC5tdy1kcm9wZG93bi5tdy1vcGVuIHtcbiAgICB0cmFuc2Zvcm06IHRyYW5zbGF0ZVkoMCk7XG4gIH1cbiAgLm13LWRyb3Bkb3duLm13LWZsaXAge1xuICAgIHRyYW5zZm9ybTogdHJhbnNsYXRlWSg0cHgpO1xuICB9XG4gIC5tdy1kcm9wZG93bi5tdy1mbGlwLm13LW9wZW4ge1xuICAgIHRyYW5zZm9ybTogdHJhbnNsYXRlWSgwKTtcbiAgfVxufVxuXG4vKiA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09XG4gICBTdGF0ZSBtZXNzYWdlcyAobG9hZGluZyAvIGVtcHR5IC8gZXJyb3IpXG4gICA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09ICovXG4ubXctc3RhdGUtbXNnIHtcbiAgcGFkZGluZzogMjBweCAxNnB4O1xuICB0ZXh0LWFsaWduOiBjZW50ZXI7XG4gIGNvbG9yOiB2YXIoLS1tZXJjdXJ5LXRleHQtbXV0ZWQpO1xuICBmb250LXNpemU6IDE0cHg7XG4gIGxpbmUtaGVpZ2h0OiAxLjU7XG59XG5cbi5tdy1zdGF0ZS1lcnJvciB7XG4gIGNvbG9yOiB2YXIoLS1tZXJjdXJ5LWVycm9yKTtcbn1cblxuLm13LWVtcHR5LWhpbnQge1xuICBtYXJnaW4tdG9wOiA4cHg7XG4gIGZvbnQtc2l6ZTogMTNweDtcbiAgY29sb3I6IHZhcigtLW1lcmN1cnktdGV4dC1tdXRlZCk7XG59XG5cbi8qIFNwaW5uZXIgKi9cbi5tdy1zcGlubmVyIHtcbiAgZGlzcGxheTogaW5saW5lLWJsb2NrO1xuICB3aWR0aDogMTZweDtcbiAgaGVpZ2h0OiAxNnB4O1xuICBib3JkZXI6IDJweCBzb2xpZCB2YXIoLS1tZXJjdXJ5LWJvcmRlcik7XG4gIGJvcmRlci10b3AtY29sb3I6IHZhcigtLW1lcmN1cnktYWNjZW50KTtcbiAgYm9yZGVyLXJhZGl1czogNTAlO1xuICB2ZXJ0aWNhbC1hbGlnbjogbWlkZGxlO1xuICBtYXJnaW4tcmlnaHQ6IDhweDtcbn1cblxuQG1lZGlhIChwcmVmZXJzLXJlZHVjZWQtbW90aW9uOiBuby1wcmVmZXJlbmNlKSB7XG4gIC5tdy1zcGlubmVyIHtcbiAgICBhbmltYXRpb246IG13LXNwaW4gMC43cyBsaW5lYXIgaW5maW5pdGU7XG4gIH1cbn1cblxuQGtleWZyYW1lcyBtdy1zcGluIHtcbiAgdG8geyB0cmFuc2Zvcm06IHJvdGF0ZSgzNjBkZWcpOyB9XG59XG5cbi8qID09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT1cbiAgIFJlc3VsdCBpdGVtc1xuICAgPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PSAqL1xuLm13LXJlc3VsdC1pdGVtIHtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAgZ2FwOiAxMnB4O1xuICBwYWRkaW5nOiAxMHB4IDE0cHg7XG4gIGN1cnNvcjogcG9pbnRlcjtcbiAgYm9yZGVyLWJvdHRvbTogMXB4IHNvbGlkIHZhcigtLW1lcmN1cnktYm9yZGVyKTtcbiAgdHJhbnNpdGlvbjogYmFja2dyb3VuZCAwLjEycyBlYXNlO1xuICAvKiBNaW5pbXVtIHRvdWNoIHRhcmdldCAqL1xuICBtaW4taGVpZ2h0OiA1NnB4O1xuICB0ZXh0LWRlY29yYXRpb246IG5vbmU7XG4gIGNvbG9yOiBpbmhlcml0O1xufVxuXG4ubXctcmVzdWx0LWl0ZW06bGFzdC1jaGlsZCB7XG4gIGJvcmRlci1ib3R0b206IG5vbmU7XG59XG5cbi5tdy1yZXN1bHQtaXRlbTpob3Zlcixcbi5tdy1yZXN1bHQtaXRlbS5tdy1zZWxlY3RlZCB7XG4gIGJhY2tncm91bmQ6IHZhcigtLW1lcmN1cnktaG92ZXIpO1xufVxuXG4ubXctcmVzdWx0LWl0ZW06Zm9jdXMtdmlzaWJsZSB7XG4gIG91dGxpbmU6IDJweCBzb2xpZCB2YXIoLS1tZXJjdXJ5LWFjY2VudCk7XG4gIG91dGxpbmUtb2Zmc2V0OiAtMnB4O1xufVxuXG4vKiBJbWFnZSB3cmFwcGVyIFx1MjAxMyBmaXhlZCBkaW1lbnNpb25zIHByZXZlbnQgbGF5b3V0IHNoaWZ0ICovXG4ubXctaW1nLXdyYXAge1xuICBmbGV4LXNocmluazogMDtcbiAgd2lkdGg6IDQ4cHg7XG4gIGhlaWdodDogNDhweDtcbiAgYm9yZGVyLXJhZGl1czogNnB4O1xuICBvdmVyZmxvdzogaGlkZGVuO1xuICBiYWNrZ3JvdW5kOiB2YXIoLS1tZXJjdXJ5LWhvdmVyKTtcbiAgZGlzcGxheTogZmxleDtcbiAgYWxpZ24taXRlbXM6IGNlbnRlcjtcbiAganVzdGlmeS1jb250ZW50OiBjZW50ZXI7XG59XG5cbi5tdy1pbWcge1xuICB3aWR0aDogNDhweDtcbiAgaGVpZ2h0OiA0OHB4O1xuICBvYmplY3QtZml0OiBjb3ZlcjtcbiAgZGlzcGxheTogYmxvY2s7XG59XG5cbi5tdy1pbWctcGxhY2Vob2xkZXIge1xuICBmb250LXNpemU6IDIycHg7XG4gIGxpbmUtaGVpZ2h0OiAxO1xuICBjb2xvcjogdmFyKC0tbWVyY3VyeS10ZXh0LW11dGVkKTtcbiAgdXNlci1zZWxlY3Q6IG5vbmU7XG59XG5cbi8qIENvbnRlbnQgYXJlYSAqL1xuLm13LXJlc3VsdC1jb250ZW50IHtcbiAgZmxleDogMTtcbiAgbWluLXdpZHRoOiAwOyAgICAgICAgIC8qIEFsbG93IHRleHQgdHJ1bmNhdGlvbiAqL1xuICBvdmVyZmxvdzogaGlkZGVuO1xufVxuXG4ubXctcmVzdWx0LXRpdGxlIHtcbiAgZm9udC1zaXplOiAxNHB4O1xuICBmb250LXdlaWdodDogNTAwO1xuICBjb2xvcjogdmFyKC0tbWVyY3VyeS10ZXh0KTtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbiAgb3ZlcmZsb3c6IGhpZGRlbjtcbiAgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXM7XG59XG5cbi5tdy1yZXN1bHQtbWV0YSB7XG4gIGZvbnQtc2l6ZTogMTJweDtcbiAgY29sb3I6IHZhcigtLW1lcmN1cnktdGV4dC1tdXRlZCk7XG4gIG1hcmdpbi10b3A6IDJweDtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbiAgb3ZlcmZsb3c6IGhpZGRlbjtcbiAgdGV4dC1vdmVyZmxvdzogZWxsaXBzaXM7XG59XG5cbi8qIFByaWNlICsgYXZhaWxhYmlsaXR5ICovXG4ubXctcmVzdWx0LXJpZ2h0IHtcbiAgZmxleC1zaHJpbms6IDA7XG4gIHRleHQtYWxpZ246IHJpZ2h0O1xuICBkaXNwbGF5OiBmbGV4O1xuICBmbGV4LWRpcmVjdGlvbjogY29sdW1uO1xuICBhbGlnbi1pdGVtczogZmxleC1lbmQ7XG4gIGdhcDogNHB4O1xufVxuXG4ubXctcmVzdWx0LXByaWNlIHtcbiAgZm9udC1zaXplOiAxNHB4O1xuICBmb250LXdlaWdodDogNjAwO1xuICBjb2xvcjogdmFyKC0tbWVyY3VyeS10ZXh0KTtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbn1cblxuLm13LXJlc3VsdC1hdmFpbCB7XG4gIGZvbnQtc2l6ZTogMTFweDtcbiAgZm9udC13ZWlnaHQ6IDUwMDtcbiAgcGFkZGluZzogMnB4IDdweDtcbiAgYm9yZGVyLXJhZGl1czogMjBweDtcbiAgd2hpdGUtc3BhY2U6IG5vd3JhcDtcbn1cblxuLyogQ29sb3IgaXMgTk9UIHRoZSBvbmx5IGluZGljYXRvciAodGV4dCBhbHNvIGRpc3Rpbmd1aXNoZXMpICovXG4ubXctaW5zdG9jayB7XG4gIGJhY2tncm91bmQ6IHJnYmEoMjIsIDE2MywgNzQsIDAuMSk7XG4gIGNvbG9yOiAjMTU4MDNkO1xufVxuXG4ubXctb3V0c3RvY2sge1xuICBiYWNrZ3JvdW5kOiByZ2JhKDIyMCwgMzgsIDM4LCAwLjEpO1xuICBjb2xvcjogI2I5MWMxYztcbn1cblxuLyogRGFyayB0aGVtZSBvdmVycmlkZXMgZm9yIGF2YWlsYWJpbGl0eSBiYWRnZXMgKi9cbkBtZWRpYSAocHJlZmVycy1jb2xvci1zY2hlbWU6IGRhcmspIHtcbiAgOmhvc3QoOm5vdChbZGF0YS10aGVtZT1cImxpZ2h0XCJdKSkgLm13LWluc3RvY2sge1xuICAgIGNvbG9yOiAjNGFkZTgwO1xuICB9XG4gIDpob3N0KDpub3QoW2RhdGEtdGhlbWU9XCJsaWdodFwiXSkpIC5tdy1vdXRzdG9jayB7XG4gICAgY29sb3I6ICNmODcxNzE7XG4gIH1cbn1cblxuLyogPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuICAgTW9iaWxlLXNwZWNpZmljIGFkanVzdG1lbnRzXG4gICA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09ICovXG5AbWVkaWEgKG1heC13aWR0aDogNDgwcHgpIHtcbiAgLm13LXJlc3VsdC1pdGVtIHtcbiAgICBwYWRkaW5nOiAxMHB4IDEycHg7XG4gICAgZ2FwOiAxMHB4O1xuICB9XG5cbiAgLm13LXJlc3VsdC1yaWdodCB7XG4gICAgZGlzcGxheTogbm9uZTsgICAvKiBIaWRlIHByaWNlIG9uIHZlcnkgc21hbGwgc2NyZWVuczsgdGl0bGUgaXMgbW9yZSBpbXBvcnRhbnQgKi9cbiAgfVxuXG4gIC5tdy1kcm9wZG93biB7XG4gICAgbWF4LWhlaWdodDogNjB2aDtcbiAgICBib3JkZXItcmFkaXVzOiAwIDAgdmFyKC0tbWVyY3VyeS1yYWRpdXMpIHZhcigtLW1lcmN1cnktcmFkaXVzKTtcbiAgfVxuXG4gIC5tdy1yZXN1bHQtaXRlbSB7XG4gICAgbWluLWhlaWdodDogNjBweDsgIC8qIExhcmdlciB0b3VjaCB0YXJnZXQgb24gbW9iaWxlICovXG4gIH1cbn1cblxuLyogPT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PVxuICAgSGlnaC1jb250cmFzdCBtb2RlXG4gICA9PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09PT09ICovXG5AbWVkaWEgKGZvcmNlZC1jb2xvcnM6IGFjdGl2ZSkge1xuICAubXctaW5wdXQge1xuICAgIGJvcmRlcjogMnB4IHNvbGlkIEJ1dHRvblRleHQ7XG4gIH1cbiAgLm13LWlucHV0OmZvY3VzIHtcbiAgICBvdXRsaW5lOiAzcHggc29saWQgSGlnaGxpZ2h0O1xuICB9XG4gIC5tdy1yZXN1bHQtaXRlbS5tdy1zZWxlY3RlZCB7XG4gICAgYmFja2dyb3VuZDogSGlnaGxpZ2h0O1xuICAgIGNvbG9yOiBIaWdobGlnaHRUZXh0O1xuICB9XG59XG4iLCAiLyoqXG4gKiBNZXJjdXJ5IFNlYXJjaCBXaWRnZXQgXHUyMDEzIEFQSSBDbGllbnRcbiAqXG4gKiBSZXNwb25zaWJpbGl0aWVzOlxuICogLSBGZXRjaC1iYXNlZCBIVFRQIHdpdGggQWJvcnRDb250cm9sbGVyXG4gKiAtIEFib3J0RXJyb3Igc3VwcHJlc3Npb24gKG5vdCBhIHVzZXItdmlzaWJsZSBlcnJvcilcbiAqIC0gUmVxdWVzdCB0aW1lb3V0XG4gKiAtIFNhZmUgZXJyb3IgY2xhc3NpZmljYXRpb24gKG5vIHJhdyBiYWNrZW5kIHBheWxvYWRzIHN1cmZhY2VkKVxuICogLSBUZWxlbWV0cnkgdmlhIHNlbmRCZWFjb24gLyBmZXRjaCBmYWxsYmFja1xuICovXG5cbmNvbnN0IFJFUVVFU1RfVElNRU9VVF9NUyA9IDgwMDA7XG5cbi8vIEVycm9yIHR5cGVzIHN1cmZhY2VkIHRvIFVJIChzYWZlIHN0cmluZ3Mgb25seSlcbmV4cG9ydCBjb25zdCBBcGlFcnJvclR5cGUgPSB7XG4gIEFCT1JUOiAgICAnYWJvcnQnLFxuICBUSU1FT1VUOiAgJ3RpbWVvdXQnLFxuICBSQVRFX0xJTUlUOiAncmF0ZV9saW1pdCcsXG4gIEFVVEg6ICAgICAnYXV0aCcsXG4gIE5PVF9GT1VORDogJ25vdF9mb3VuZCcsXG4gIFNFUlZFUjogICAnc2VydmVyJyxcbiAgTkVUV09SSzogICduZXR3b3JrJyxcbn07XG5cbmV4cG9ydCBjbGFzcyBNZXJjdXJ5QXBpRXJyb3IgZXh0ZW5kcyBFcnJvciB7XG4gIGNvbnN0cnVjdG9yKHR5cGUsIG1lc3NhZ2UpIHtcbiAgICBzdXBlcihtZXNzYWdlKTtcbiAgICB0aGlzLnR5cGUgPSB0eXBlO1xuICAgIHRoaXMubmFtZSA9ICdNZXJjdXJ5QXBpRXJyb3InO1xuICB9XG59XG5cbi8qKlxuICogVmFsaWRhdGUgcHJvZHVjdCBVUkwgaXMgc2FmZSAobm90IGphdmFzY3JpcHQ6LCBkYXRhOiwgZXRjLilcbiAqL1xuZXhwb3J0IGZ1bmN0aW9uIGlzU2FmZVVybCh1cmwpIHtcbiAgaWYgKCF1cmwgfHwgdHlwZW9mIHVybCAhPT0gJ3N0cmluZycpIHJldHVybiBmYWxzZTtcbiAgdHJ5IHtcbiAgICBjb25zdCBwYXJzZWQgPSBuZXcgVVJMKHVybCk7XG4gICAgcmV0dXJuIHBhcnNlZC5wcm90b2NvbCA9PT0gJ2h0dHBzOicgfHwgcGFyc2VkLnByb3RvY29sID09PSAnaHR0cDonO1xuICB9IGNhdGNoIHtcbiAgICByZXR1cm4gZmFsc2U7XG4gIH1cbn1cblxuLyoqXG4gKiBHZW5lcmF0ZSBhIHN0YWJsZSBhbm9ueW1vdXMgc2Vzc2lvbiBJRCBzdG9yZWQgaW4gc2Vzc2lvblN0b3JhZ2UuXG4gKiBGYWxscyBiYWNrIHRvIGEgcmFuZG9tIHZhbHVlIGlmIHN0b3JhZ2UgaXMgdW5hdmFpbGFibGUuXG4gKi9cbmV4cG9ydCBmdW5jdGlvbiBnZXRTZXNzaW9uSWQoKSB7XG4gIHRyeSB7XG4gICAgY29uc3Qga2V5ID0gJ19fbXNpZCc7XG4gICAgbGV0IGlkID0gc2Vzc2lvblN0b3JhZ2UuZ2V0SXRlbShrZXkpO1xuICAgIGlmICghaWQpIHtcbiAgICAgIGlkID0gJ21zXycgKyBNYXRoLnJhbmRvbSgpLnRvU3RyaW5nKDM2KS5zbGljZSgyKSArIERhdGUubm93KCkudG9TdHJpbmcoMzYpO1xuICAgICAgc2Vzc2lvblN0b3JhZ2Uuc2V0SXRlbShrZXksIGlkKTtcbiAgICB9XG4gICAgcmV0dXJuIGlkO1xuICB9IGNhdGNoIHtcbiAgICByZXR1cm4gJ21zXycgKyBNYXRoLnJhbmRvbSgpLnRvU3RyaW5nKDM2KS5zbGljZSgyKTtcbiAgfVxufVxuXG5leHBvcnQgY2xhc3MgU2VhcmNoQVBJIHtcbiAgLyoqXG4gICAqIEBwYXJhbSB7c3RyaW5nfSBlbmRwb2ludCAtIEJhc2UgVVJMICh0cmFpbGluZyBzbGFzaCBzdHJpcHBlZClcbiAgICogQHBhcmFtIHtzdHJpbmd9IGFwaUtleSAgIC0gUHVibGljIHBrXyoga2V5IG9ubHlcbiAgICovXG4gIGNvbnN0cnVjdG9yKGVuZHBvaW50LCBhcGlLZXkpIHtcbiAgICAvLyBOb3JtYWxpemUgZW5kcG9pbnRcbiAgICB0aGlzLmVuZHBvaW50ID0gKGVuZHBvaW50IHx8IHdpbmRvdy5sb2NhdGlvbi5vcmlnaW4pLnJlcGxhY2UoL1xcLyQvLCAnJyk7XG4gICAgdGhpcy5hcGlLZXkgPSBhcGlLZXk7XG4gICAgdGhpcy5fYWN0aXZlQ29udHJvbGxlciA9IG51bGw7XG4gIH1cblxuICAvKipcbiAgICogRXhlY3V0ZSBhIHByb2R1Y3Qgc2VhcmNoLiBDYW5jZWxzIGFueSBpbi1mbGlnaHQgc2VhcmNoIGZpcnN0LlxuICAgKiBAcGFyYW0ge3N0cmluZ30gcXVlcnlcbiAgICogQHBhcmFtIHtudW1iZXJ9IGxpbWl0XG4gICAqIEByZXR1cm5zIHtQcm9taXNlPHtyZXN1bHRzOiBBcnJheSwgc2VhcmNoSWQ6IHN0cmluZ3xudWxsfT59XG4gICAqL1xuICBhc3luYyBzZWFyY2gocXVlcnksIGxpbWl0ID0gOCkge1xuICAgIC8vIEFib3J0IHByZXZpb3VzIGluLWZsaWdodCBzZWFyY2hcbiAgICBpZiAodGhpcy5fYWN0aXZlQ29udHJvbGxlcikge1xuICAgICAgdGhpcy5fYWN0aXZlQ29udHJvbGxlci5hYm9ydCgpO1xuICAgIH1cbiAgICBjb25zdCBjb250cm9sbGVyID0gbmV3IEFib3J0Q29udHJvbGxlcigpO1xuICAgIHRoaXMuX2FjdGl2ZUNvbnRyb2xsZXIgPSBjb250cm9sbGVyO1xuXG4gICAgY29uc3QgdGltZXIgPSBzZXRUaW1lb3V0KCgpID0+IGNvbnRyb2xsZXIuYWJvcnQoKSwgUkVRVUVTVF9USU1FT1VUX01TKTtcblxuICAgIHRyeSB7XG4gICAgICBjb25zdCB1cmwgPSBuZXcgVVJMKCcvYXBpL3YxL3dpZGdldC9zZWFyY2gvaW5zdGFudCcsIHRoaXMuZW5kcG9pbnQpO1xuICAgICAgdXJsLnNlYXJjaFBhcmFtcy5zZXQoJ3EnLCBxdWVyeSk7XG4gICAgICB1cmwuc2VhcmNoUGFyYW1zLnNldCgnbGltaXQnLCBTdHJpbmcoTWF0aC5taW4obGltaXQsIDUwKSkpO1xuXG4gICAgICBjb25zdCByZXNwb25zZSA9IGF3YWl0IGZldGNoKHVybC50b1N0cmluZygpLCB7XG4gICAgICAgIG1ldGhvZDogJ0dFVCcsXG4gICAgICAgIGhlYWRlcnM6IHtcbiAgICAgICAgICAnWC1BUEktS2V5JzogdGhpcy5hcGlLZXksXG4gICAgICAgICAgJ0FjY2VwdCc6ICdhcHBsaWNhdGlvbi9qc29uJyxcbiAgICAgICAgfSxcbiAgICAgICAgc2lnbmFsOiBjb250cm9sbGVyLnNpZ25hbCxcbiAgICAgIH0pO1xuXG4gICAgICBjbGVhclRpbWVvdXQodGltZXIpO1xuICAgICAgdGhpcy5fYWN0aXZlQ29udHJvbGxlciA9IG51bGw7XG5cbiAgICAgIHJldHVybiBhd2FpdCB0aGlzLl9oYW5kbGVTZWFyY2hSZXNwb25zZShyZXNwb25zZSk7XG4gICAgfSBjYXRjaCAoZXJyKSB7XG4gICAgICBjbGVhclRpbWVvdXQodGltZXIpO1xuICAgICAgdGhpcy5fYWN0aXZlQ29udHJvbGxlciA9IG51bGw7XG5cbiAgICAgIGlmIChlcnIubmFtZSA9PT0gJ0Fib3J0RXJyb3InKSB7XG4gICAgICAgIHRocm93IG5ldyBNZXJjdXJ5QXBpRXJyb3IoQXBpRXJyb3JUeXBlLkFCT1JULCAnUmVxdWVzdCBjYW5jZWxsZWQnKTtcbiAgICAgIH1cbiAgICAgIHRocm93IG5ldyBNZXJjdXJ5QXBpRXJyb3IoQXBpRXJyb3JUeXBlLk5FVFdPUkssICdOZXR3b3JrIGVycm9yLiBQbGVhc2UgY2hlY2sgeW91ciBjb25uZWN0aW9uLicpO1xuICAgIH1cbiAgfVxuXG4gIGFzeW5jIF9oYW5kbGVTZWFyY2hSZXNwb25zZShyZXNwb25zZSkge1xuICAgIGlmIChyZXNwb25zZS5zdGF0dXMgPT09IDQyOSkge1xuICAgICAgdGhyb3cgbmV3IE1lcmN1cnlBcGlFcnJvcihBcGlFcnJvclR5cGUuUkFURV9MSU1JVCwgJ1RvbyBtYW55IHJlcXVlc3RzLiBQbGVhc2Ugd2FpdCBhIG1vbWVudCBhbmQgdHJ5IGFnYWluLicpO1xuICAgIH1cbiAgICBpZiAocmVzcG9uc2Uuc3RhdHVzID09PSA0MDEgfHwgcmVzcG9uc2Uuc3RhdHVzID09PSA0MDMpIHtcbiAgICAgIHRocm93IG5ldyBNZXJjdXJ5QXBpRXJyb3IoQXBpRXJyb3JUeXBlLkFVVEgsICdTZWFyY2ggdW5hdmFpbGFibGUuIFBsZWFzZSBjb250YWN0IHRoZSBzdG9yZSBvd25lci4nKTtcbiAgICB9XG4gICAgaWYgKHJlc3BvbnNlLnN0YXR1cyA9PT0gNDA0KSB7XG4gICAgICB0aHJvdyBuZXcgTWVyY3VyeUFwaUVycm9yKEFwaUVycm9yVHlwZS5OT1RfRk9VTkQsICdTZWFyY2ggc2VydmljZSBub3QgZm91bmQuJyk7XG4gICAgfVxuICAgIGlmICghcmVzcG9uc2Uub2spIHtcbiAgICAgIHRocm93IG5ldyBNZXJjdXJ5QXBpRXJyb3IoQXBpRXJyb3JUeXBlLlNFUlZFUiwgJ1NlYXJjaCBpcyB0ZW1wb3JhcmlseSB1bmF2YWlsYWJsZS4gUGxlYXNlIHRyeSBhZ2Fpbi4nKTtcbiAgICB9XG5cbiAgICBsZXQgZGF0YTtcbiAgICB0cnkge1xuICAgICAgZGF0YSA9IGF3YWl0IHJlc3BvbnNlLmpzb24oKTtcbiAgICB9IGNhdGNoIHtcbiAgICAgIHRocm93IG5ldyBNZXJjdXJ5QXBpRXJyb3IoQXBpRXJyb3JUeXBlLlNFUlZFUiwgJ1VuZXhwZWN0ZWQgcmVzcG9uc2UgZnJvbSBzZXJ2ZXIuJyk7XG4gICAgfVxuXG4gICAgLy8gU2FuaXRpemUgYW5kIHZhbGlkYXRlIGVhY2ggcmVzdWx0IFx1MjAxNCBuZXZlciB0cnVzdCBiYWNrZW5kIHZhbHVlcyBhcyBIVE1MXG4gICAgY29uc3QgcmF3ID0gQXJyYXkuaXNBcnJheShkYXRhLnN1Z2dlc3Rpb25zKSA/IGRhdGEuc3VnZ2VzdGlvbnMgOiBbXTtcbiAgICBjb25zdCByZXN1bHRzID0gcmF3Lm1hcChpdGVtID0+IHRoaXMuX3Nhbml0aXplUHJvZHVjdChpdGVtKSk7XG5cbiAgICByZXR1cm4ge1xuICAgICAgcmVzdWx0cyxcbiAgICAgIHNlYXJjaElkOiAoZGF0YS5zZWFyY2hfaWQgJiYgdHlwZW9mIGRhdGEuc2VhcmNoX2lkID09PSAnc3RyaW5nJykgPyBkYXRhLnNlYXJjaF9pZCA6IG51bGwsXG4gICAgfTtcbiAgfVxuXG4gIC8qKlxuICAgKiBSZXR1cm4gYSBzYWZlIHByb2R1Y3Qgb2JqZWN0IHdpdGggb25seSB3aGl0ZWxpc3RlZCBmaWVsZHMuXG4gICAqIEFsbCBzdHJpbmcgdmFsdWVzIGdvIHRocm91Z2ggdGhlIHNhZmUgdGV4dCBwYXRoLlxuICAgKi9cbiAgX3Nhbml0aXplUHJvZHVjdChpdGVtKSB7XG4gICAgaWYgKCFpdGVtIHx8IHR5cGVvZiBpdGVtICE9PSAnb2JqZWN0JykgcmV0dXJuIG51bGw7XG5cbiAgICBjb25zdCB0aXRsZSAgID0gdHlwZW9mIGl0ZW0udGl0bGUgID09PSAnc3RyaW5nJyA/IGl0ZW0udGl0bGUudHJpbSgpICA6ICcnO1xuICAgIGNvbnN0IGJyYW5kICAgPSB0eXBlb2YgaXRlbS5icmFuZCAgPT09ICdzdHJpbmcnID8gaXRlbS5icmFuZC50cmltKCkgIDogJyc7XG4gICAgY29uc3QgY2F0ZWdvcnkgPSB0eXBlb2YgaXRlbS5jYXRlZ29yeSA9PT0gJ3N0cmluZycgPyBpdGVtLmNhdGVnb3J5LnRyaW0oKSA6ICcnO1xuICAgIGNvbnN0IHByaWNlICAgPSB0eXBlb2YgaXRlbS5wcmljZSAgPT09ICdudW1iZXInID8gaXRlbS5wcmljZSAgOlxuICAgICAgICAgICAgICAgICAgICB0eXBlb2YgaXRlbS5zZWxsaW5nX3ByaWNlID09PSAnbnVtYmVyJyA/IGl0ZW0uc2VsbGluZ19wcmljZSA6IG51bGw7XG4gICAgY29uc3QgaW5TdG9jayA9IHR5cGVvZiBpdGVtLmluX3N0b2NrID09PSAnYm9vbGVhbicgPyBpdGVtLmluX3N0b2NrIDpcbiAgICAgICAgICAgICAgICAgICAgKGl0ZW0uc3RvY2sgPT09IHRydWUgfHwgaXRlbS5zdG9jayA9PT0gMSk7XG5cbiAgICAvLyBWYWxpZGF0ZSBpbWFnZSBVUkwgXHUyMDEzIG9ubHkgYWxsb3cgaHR0cC9odHRwc1xuICAgIGNvbnN0IHJhd0ltYWdlID0gaXRlbS5pbWFnZV91cmwgfHwgaXRlbS5pbWFnZSB8fCAnJztcbiAgICBjb25zdCBpbWFnZVVybCA9IGlzU2FmZVVybChyYXdJbWFnZSkgPyByYXdJbWFnZSA6ICcnO1xuXG4gICAgLy8gVmFsaWRhdGUgcHJvZHVjdCBVUkxcbiAgICBjb25zdCByYXdVcmwgPSBpdGVtLnVybCB8fCBpdGVtLnByb2R1Y3RfdXJsIHx8ICcnO1xuICAgIGNvbnN0IHByb2R1Y3RVcmwgPSBpc1NhZmVVcmwocmF3VXJsKSA/IHJhd1VybCA6ICcnO1xuXG4gICAgY29uc3QgaWQgPSB0eXBlb2YgaXRlbS5pZCA9PT0gJ3N0cmluZycgPyBpdGVtLmlkIDpcbiAgICAgICAgICAgICAgIHR5cGVvZiBpdGVtLmlkID09PSAnbnVtYmVyJyA/IFN0cmluZyhpdGVtLmlkKSA6ICcnO1xuXG4gICAgcmV0dXJuIHsgaWQsIHRpdGxlLCBicmFuZCwgY2F0ZWdvcnksIHByaWNlLCBpblN0b2NrLCBpbWFnZVVybCwgcHJvZHVjdFVybCB9O1xuICB9XG5cbiAgLyoqXG4gICAqIENhbmNlbCBhbnkgcGVuZGluZyBzZWFyY2ggcmVxdWVzdC5cbiAgICovXG4gIGNhbmNlbFNlYXJjaCgpIHtcbiAgICBpZiAodGhpcy5fYWN0aXZlQ29udHJvbGxlcikge1xuICAgICAgdGhpcy5fYWN0aXZlQ29udHJvbGxlci5hYm9ydCgpO1xuICAgICAgdGhpcy5fYWN0aXZlQ29udHJvbGxlciA9IG51bGw7XG4gICAgfVxuICB9XG5cbiAgLyoqXG4gICAqIEdldCB3aWRnZXQgY29uZmlnIGZyb20gdGhlIGJhY2tlbmQuXG4gICAqIE5vbi1ibG9ja2luZzogZmFpbHVyZXMgcmV0dXJuIGRlZmF1bHRzLlxuICAgKi9cbiAgYXN5bmMgZ2V0V2lkZ2V0Q29uZmlnKCkge1xuICAgIHRyeSB7XG4gICAgICBjb25zdCB1cmwgPSBuZXcgVVJMKCcvYXBpL3YxL3dpZGdldC9jb25maWcnLCB0aGlzLmVuZHBvaW50KTtcbiAgICAgIGNvbnN0IGNvbnRyb2xsZXIgPSBuZXcgQWJvcnRDb250cm9sbGVyKCk7XG4gICAgICBjb25zdCB0aW1lciA9IHNldFRpbWVvdXQoKCkgPT4gY29udHJvbGxlci5hYm9ydCgpLCA1MDAwKTtcblxuICAgICAgY29uc3QgcmVzcG9uc2UgPSBhd2FpdCBmZXRjaCh1cmwudG9TdHJpbmcoKSwge1xuICAgICAgICBoZWFkZXJzOiB7ICdYLUFQSS1LZXknOiB0aGlzLmFwaUtleSwgJ0FjY2VwdCc6ICdhcHBsaWNhdGlvbi9qc29uJyB9LFxuICAgICAgICBzaWduYWw6IGNvbnRyb2xsZXIuc2lnbmFsLFxuICAgICAgfSk7XG4gICAgICBjbGVhclRpbWVvdXQodGltZXIpO1xuXG4gICAgICBpZiAoIXJlc3BvbnNlLm9rKSByZXR1cm4gbnVsbDtcbiAgICAgIGNvbnN0IGRhdGEgPSBhd2FpdCByZXNwb25zZS5qc29uKCk7XG4gICAgICByZXR1cm4gZGF0YS5zdWNjZXNzID8gZGF0YS5jb25maWcgOiBudWxsO1xuICAgIH0gY2F0Y2gge1xuICAgICAgcmV0dXJuIG51bGw7XG4gICAgfVxuICB9XG5cbiAgLyoqXG4gICAqIEZpcmUgYSB0ZWxlbWV0cnkgZXZlbnQuXG4gICAqIE5ldmVyIGJsb2NrcyBuYXZpZ2F0aW9uOyB1c2VzIHNlbmRCZWFjb24gd2hlbiBhdmFpbGFibGUuXG4gICAqIEBwYXJhbSB7b2JqZWN0fSBldmVudCAtIHNhZmUgZXZlbnQgcGF5bG9hZFxuICAgKi9cbiAgc2VuZFRlbGVtZXRyeShldmVudCkge1xuICAgIHRyeSB7XG4gICAgICBjb25zdCB1cmwgPSBuZXcgVVJMKCcvYXBpL3YxL3RlbGVtZXRyeS9ldmVudHMnLCB0aGlzLmVuZHBvaW50KS50b1N0cmluZygpO1xuICAgICAgY29uc3QgYm9keSA9IEpTT04uc3RyaW5naWZ5KHtcbiAgICAgICAgZXZlbnRfdHlwZTogZXZlbnQuZXZlbnQgfHwgJ3Vua25vd24nLFxuICAgICAgICBwcm9kdWN0X2lkOiBldmVudC5wcm9kdWN0SWQgfHwgbnVsbCxcbiAgICAgICAgcXVlcnk6IGV2ZW50LnF1ZXJ5IHx8IG51bGwsXG4gICAgICAgIHNlYXJjaF9pZDogZXZlbnQuc2VhcmNoSWQgfHwgbnVsbCxcbiAgICAgICAgdXNlcl9pZDogZXZlbnQuc2Vzc2lvbklkIHx8IG51bGwsXG4gICAgICAgIG1ldGFkYXRhOiB7XG4gICAgICAgICAgcG9zaXRpb246IGV2ZW50LnBvc2l0aW9uIHx8IG51bGwsXG4gICAgICAgICAgdGltZXN0YW1wOiBuZXcgRGF0ZSgpLnRvSVNPU3RyaW5nKCksXG4gICAgICAgIH0sXG4gICAgICB9KTtcblxuICAgICAgLy8gUHJlZmVyIHNlbmRCZWFjb24gZm9yIGNsaWNrL25hdmlnYXRpb24gZXZlbnRzIChub24tYmxvY2tpbmcpXG4gICAgICBpZiAobmF2aWdhdG9yLnNlbmRCZWFjb24pIHtcbiAgICAgICAgY29uc3QgYmxvYiA9IG5ldyBCbG9iKFtib2R5XSwgeyB0eXBlOiAnYXBwbGljYXRpb24vanNvbicgfSk7XG4gICAgICAgIC8vIHNlbmRCZWFjb24gcmVxdWlyZXMgaGVhZGVycyB3b3JrYXJvdW5kIHZpYSBCbG9iIFx1MjAxMyBhdHRhY2ggQVBJIGtleSB2aWEgVVJMIHBhcmFtXG4gICAgICAgIGNvbnN0IGJlYWNvblVybCA9IHVybCArICc/az0nICsgZW5jb2RlVVJJQ29tcG9uZW50KHRoaXMuYXBpS2V5KTtcbiAgICAgICAgLy8gVHJ5IHNlbmRCZWFjb24gZmlyc3QsIGZhbGwgYmFjayB0byBmZXRjaFxuICAgICAgICBjb25zdCBzZW50ID0gbmF2aWdhdG9yLnNlbmRCZWFjb24oYmVhY29uVXJsLCBibG9iKTtcbiAgICAgICAgaWYgKHNlbnQpIHJldHVybjtcbiAgICAgIH1cblxuICAgICAgLy8gRmV0Y2ggZmFsbGJhY2sgKGZpcmUtYW5kLWZvcmdldClcbiAgICAgIGZldGNoKHVybCwge1xuICAgICAgICBtZXRob2Q6ICdQT1NUJyxcbiAgICAgICAgaGVhZGVyczoge1xuICAgICAgICAgICdDb250ZW50LVR5cGUnOiAnYXBwbGljYXRpb24vanNvbicsXG4gICAgICAgICAgJ1gtQVBJLUtleSc6IHRoaXMuYXBpS2V5LFxuICAgICAgICB9LFxuICAgICAgICBib2R5LFxuICAgICAgICBrZWVwYWxpdmU6IHRydWUsXG4gICAgICB9KS5jYXRjaCgoKSA9PiB7IC8qIHRlbGVtZXRyeSBmYWlsdXJlIGlzIG5vbi1mYXRhbCAqLyB9KTtcbiAgICB9IGNhdGNoIHtcbiAgICAgIC8vIFRlbGVtZXRyeSBtdXN0IG5ldmVyIHRocm93XG4gICAgfVxuICB9XG59XG4iLCAiLyoqXG4gKiBNZXJjdXJ5IFNlYXJjaCBXaWRnZXQgXHUyMDEzIFNoYWRvdyBET00gVUkgQ29tcG9uZW50XG4gKlxuICogSW1wbGVtZW50cyBhIDxtZXJjdXJ5LXNlYXJjaD4gV2ViIENvbXBvbmVudCB3aXRoOlxuICogLSBGdWxsIFNoYWRvdyBET00gQ1NTIGlzb2xhdGlvblxuICogLSBBY2Nlc3NpYmxlIGNvbWJvYm94L2xpc3Rib3ggcGF0dGVyblxuICogLSBLZXlib2FyZCBuYXZpZ2F0aW9uIChBcnJvdywgRW50ZXIsIEVzY2FwZSwgVGFiKVxuICogLSBEZWJvdW5jZWQgc2VhcmNoIHdpdGggQWJvcnRDb250cm9sbGVyXG4gKiAtIFNhZmUgdGV4dCByZW5kZXJpbmcgKG5vIGlubmVySFRNTCB3aXRoIHVudHJ1c3RlZCBkYXRhKVxuICogLSBMb2FkaW5nLCBuby1yZXN1bHRzLCBlcnJvciwgYW5kIG9mZmxpbmUgc3RhdGVzXG4gKiAtIENsaWNrIHRlbGVtZXRyeSAobm9uLWJsb2NraW5nKVxuICogLSBXQ0FHIEFBIGZvY3VzIGluZGljYXRvcnMsIEFSSUEgYXR0cmlidXRlc1xuICogLSBWaWV3cG9ydC1hd2FyZSBkcm9wZG93biBwb3NpdGlvbmluZ1xuICogLSBwcmVmZXJzLXJlZHVjZWQtbW90aW9uIHN1cHBvcnRcbiAqIC0gQ1NTIHZhcmlhYmxlIHRoZW1pbmcgdmlhIDpob3N0XG4gKiAtIExpZmVjeWNsZTogZGVzdHJveSgpIGNsZWFucyB1cCBhbGwgbGlzdGVuZXJzL3RpbWVycy9yZXF1ZXN0c1xuICovXG5cbmltcG9ydCBjc3MgZnJvbSAnLi9zdHlsZXMuY3NzJztcbmltcG9ydCB7IFNlYXJjaEFQSSwgTWVyY3VyeUFwaUVycm9yLCBBcGlFcnJvclR5cGUsIGdldFNlc3Npb25JZCB9IGZyb20gJy4vYXBpLmpzJztcblxuLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4vLyBTYWZlIHRleHQgaGVscGVycyBcdTIwMTMgbmV2ZXIgdXNlIGlubmVySFRNTCB3aXRoIHVudHJ1c3RlZCB2YWx1ZXNcbi8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuZnVuY3Rpb24gc2V0VGV4dChlbCwgdGV4dCkge1xuICBlbC50ZXh0Q29udGVudCA9IHR5cGVvZiB0ZXh0ID09PSAnc3RyaW5nJyA/IHRleHQgOiBTdHJpbmcodGV4dCA/PyAnJyk7XG59XG5cbmZ1bmN0aW9uIGNyZWF0ZUVsKHRhZywgYXR0cnMgPSB7fSwgdGV4dENvbnRlbnQpIHtcbiAgY29uc3QgZWwgPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50KHRhZyk7XG4gIGZvciAoY29uc3QgW2ssIHZdIG9mIE9iamVjdC5lbnRyaWVzKGF0dHJzKSkge1xuICAgIGlmIChrID09PSAnY2xhc3NOYW1lJykgZWwuY2xhc3NOYW1lID0gdjtcbiAgICBlbHNlIGlmIChrID09PSAncm9sZScgfHwgayA9PT0gJ2FyaWEtbGFiZWwnIHx8IGsgPT09ICdhcmlhLWV4cGFuZGVkJyB8fFxuICAgICAgICAgICAgIGsgPT09ICdhcmlhLWFjdGl2ZWRlc2NlbmRhbnQnIHx8IGsgPT09ICdhcmlhLWNvbnRyb2xzJyB8fFxuICAgICAgICAgICAgIGsgPT09ICdhcmlhLXNlbGVjdGVkJyB8fCBrID09PSAnYXJpYS1saXZlJyB8fCBrID09PSAnYXJpYS1hdG9taWMnIHx8XG4gICAgICAgICAgICAgayA9PT0gJ2FyaWEtYnVzeScgfHwgayA9PT0gJ2FyaWEtaGFzcG9wdXAnIHx8IGsgPT09ICdhcmlhLWF1dG9jb21wbGV0ZScpIHtcbiAgICAgIGVsLnNldEF0dHJpYnV0ZShrLCB2KTtcbiAgICB9IGVsc2Uge1xuICAgICAgZWxba10gPSB2O1xuICAgIH1cbiAgfVxuICBpZiAodGV4dENvbnRlbnQgIT09IHVuZGVmaW5lZCkgc2V0VGV4dChlbCwgdGV4dENvbnRlbnQpO1xuICByZXR1cm4gZWw7XG59XG5cbi8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuLy8gRGVib3VuY2Vcbi8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuZnVuY3Rpb24gZGVib3VuY2UoZm4sIHdhaXQpIHtcbiAgbGV0IHQ7XG4gIHJldHVybiBmdW5jdGlvbiAoLi4uYXJncykge1xuICAgIGNsZWFyVGltZW91dCh0KTtcbiAgICB0ID0gc2V0VGltZW91dCgoKSA9PiBmbi5hcHBseSh0aGlzLCBhcmdzKSwgd2FpdCk7XG4gIH07XG59XG5cbi8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuLy8gTWVyY3VyeVNlYXJjaEVsZW1lbnQgXHUyMDEzIHRoZSBXZWIgQ29tcG9uZW50XG4vLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbmV4cG9ydCBjbGFzcyBNZXJjdXJ5U2VhcmNoRWxlbWVudCBleHRlbmRzIEhUTUxFbGVtZW50IHtcbiAgY29uc3RydWN0b3IoKSB7XG4gICAgc3VwZXIoKTtcbiAgICB0aGlzLl9zaGFkb3cgPSB0aGlzLmF0dGFjaFNoYWRvdyh7IG1vZGU6ICdvcGVuJyB9KTtcbiAgICB0aGlzLl9hcGkgPSBudWxsO1xuICAgIHRoaXMuX2NvbmZpZyA9IG51bGw7XG4gICAgdGhpcy5fc3RhdGUgPSB7XG4gICAgICBxdWVyeTogJycsXG4gICAgICByZXN1bHRzOiBbXSxcbiAgICAgIHNlbGVjdGVkSW5kZXg6IC0xLFxuICAgICAgaXNMb2FkaW5nOiBmYWxzZSxcbiAgICAgIGlzT3BlbjogZmFsc2UsXG4gICAgICBlcnJvcjogbnVsbCwgICAvLyBudWxsIHwgc3RyaW5nIChzYWZlIG1lc3NhZ2UpXG4gICAgICBzZWFyY2hJZDogbnVsbCxcbiAgICB9O1xuICAgIHRoaXMuX3Nlc3Npb25JZCA9IGdldFNlc3Npb25JZCgpO1xuICAgIHRoaXMuX2xpc3RlbmVycyA9IFtdOyAvLyB7IHRhcmdldCwgdHlwZSwgZm4sIG9wdHM/IH1cbiAgICB0aGlzLl90aW1lcnMgPSBbXTtcbiAgICB0aGlzLl9kZWJvdW5jZVNlYXJjaCA9IG51bGw7XG4gICAgdGhpcy5fbGFzdENsaWNrZWRQcm9kdWN0SWQgPSBudWxsOyAvLyBmb3IgZGVkdXBcbiAgICB0aGlzLl9sYXN0Q2xpY2tUcyA9IDA7XG4gICAgdGhpcy5fZWxzID0ge307XG4gIH1cblxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgLy8gV2ViIENvbXBvbmVudCBsaWZlY3ljbGVcbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIGNvbm5lY3RlZENhbGxiYWNrKCkge1xuICAgIC8vIENvbmZpZyBtYXkgaGF2ZSBiZWVuIHNldCBieSBpbmRleC5qcyBiZWZvcmUgY29ubmVjdGVkQ2FsbGJhY2tcbiAgICBpZiAodGhpcy5fbWVyY3VyeUNvbmZpZykge1xuICAgICAgdGhpcy5jb25maWd1cmUodGhpcy5fbWVyY3VyeUNvbmZpZyk7XG4gICAgfVxuICB9XG5cbiAgZGlzY29ubmVjdGVkQ2FsbGJhY2soKSB7XG4gICAgdGhpcy5kZXN0cm95KCk7XG4gIH1cblxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgLy8gUHVibGljIEFQSVxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cblxuICBjb25maWd1cmUoY29uZmlnKSB7XG4gICAgaWYgKHRoaXMuX2NvbmZpZykgcmV0dXJuOyAvLyBhbHJlYWR5IGNvbmZpZ3VyZWQgKGlkZW1wb3RlbnQpXG4gICAgdGhpcy5fY29uZmlnID0gY29uZmlnO1xuICAgIHRoaXMuX2FwaSA9IG5ldyBTZWFyY2hBUEkoY29uZmlnLmVuZHBvaW50LCBjb25maWcuYXBpS2V5KTtcbiAgICB0aGlzLl9kZWJvdW5jZVNlYXJjaCA9IGRlYm91bmNlKHRoaXMuX2V4ZWN1dGVTZWFyY2guYmluZCh0aGlzKSwgY29uZmlnLmRlYm91bmNlIHx8IDIwMCk7XG5cbiAgICB0aGlzLl9idWlsZFNoYWRvdygpO1xuICAgIHRoaXMuX2JpbmRFdmVudHMoKTtcbiAgICB0aGlzLl9zZW5kVGVsZW1ldHJ5KHsgZXZlbnQ6ICd3aWRnZXRfbG9hZGVkJyB9KTtcblxuICAgIC8vIE9wdGlvbmFsbHkgZmV0Y2ggcmVtb3RlIHRoZW1lIG92ZXJyaWRlIChub24tYmxvY2tpbmcpXG4gICAgdGhpcy5fYXBpLmdldFdpZGdldENvbmZpZygpLnRoZW4oY2ZnID0+IHtcbiAgICAgIGlmIChjZmcpIHRoaXMuX2FwcGx5UmVtb3RlVGhlbWUoY2ZnKTtcbiAgICB9KTtcbiAgfVxuXG4gIGRlc3Ryb3koKSB7XG4gICAgLy8gQ2FuY2VsIHJlcXVlc3RzXG4gICAgaWYgKHRoaXMuX2FwaSkgdGhpcy5fYXBpLmNhbmNlbFNlYXJjaCgpO1xuXG4gICAgLy8gQ2xlYXIgbGlzdGVuZXJzXG4gICAgZm9yIChjb25zdCB7IHRhcmdldCwgdHlwZSwgZm4sIG9wdHMgfSBvZiB0aGlzLl9saXN0ZW5lcnMpIHtcbiAgICAgIHRhcmdldC5yZW1vdmVFdmVudExpc3RlbmVyKHR5cGUsIGZuLCBvcHRzKTtcbiAgICB9XG4gICAgdGhpcy5fbGlzdGVuZXJzID0gW107XG5cbiAgICAvLyBDbGVhciB0aW1lcnNcbiAgICBmb3IgKGNvbnN0IGlkIG9mIHRoaXMuX3RpbWVycykgY2xlYXJUaW1lb3V0KGlkKTtcbiAgICB0aGlzLl90aW1lcnMgPSBbXTtcblxuICAgIC8vIENsZWFyIHNoYWRvdyBET01cbiAgICB0aGlzLl9zaGFkb3cuaW5uZXJIVE1MID0gJyc7XG4gICAgdGhpcy5fZWxzID0ge307XG4gICAgdGhpcy5fY29uZmlnID0gbnVsbDtcbiAgICB0aGlzLl9hcGkgPSBudWxsO1xuICB9XG5cbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIC8vIFNoYWRvdyBET00gY29uc3RydWN0aW9uXG4gIC8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuICBfYnVpbGRTaGFkb3coKSB7XG4gICAgY29uc3Qgc2hhZG93ID0gdGhpcy5fc2hhZG93O1xuICAgIHNoYWRvdy5pbm5lckhUTUwgPSAnJztcblxuICAgIC8vIFN0eWxlcyAoc2NvcGVkIGluc2lkZSBzaGFkb3cpXG4gICAgY29uc3Qgc3R5bGVFbCA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ3N0eWxlJyk7XG4gICAgc3R5bGVFbC50ZXh0Q29udGVudCA9IGNzcztcbiAgICBzaGFkb3cuYXBwZW5kQ2hpbGQoc3R5bGVFbCk7XG5cbiAgICAvLyBIb3N0IHdyYXBwZXIgKGJsb2NrLCBubyBsYXlvdXQgc2hpZnQpXG4gICAgY29uc3Qgd3JhcHBlciA9IGNyZWF0ZUVsKCdkaXYnLCB7IGNsYXNzTmFtZTogJ213LXdyYXBwZXInIH0pO1xuXG4gICAgLy8gLS0tIElucHV0IHJvdyAtLS1cbiAgICBjb25zdCBpbnB1dFJvdyA9IGNyZWF0ZUVsKCdkaXYnLCB7IGNsYXNzTmFtZTogJ213LWlucHV0LXJvdycgfSk7XG5cbiAgICAvLyBWaXN1YWxseSBoaWRkZW4gbGFiZWwgZm9yIGFjY2Vzc2liaWxpdHlcbiAgICBjb25zdCBsYWJlbCA9IGNyZWF0ZUVsKCdsYWJlbCcsIHtcbiAgICAgIGNsYXNzTmFtZTogJ213LWxhYmVsJyxcbiAgICAgIGh0bWxGb3I6ICdtdy1pbnB1dCcsXG4gICAgfSwgJ1NlYXJjaCBwcm9kdWN0cycpO1xuXG4gICAgLy8gU2VhcmNoIGljb25cbiAgICBjb25zdCBzZWFyY2hJY29uID0gdGhpcy5fbWFrZVNlYXJjaEljb24oKTtcblxuICAgIC8vIElucHV0XG4gICAgY29uc3QgaW5wdXQgPSBjcmVhdGVFbCgnaW5wdXQnLCB7XG4gICAgICBpZDogJ213LWlucHV0JyxcbiAgICAgIHR5cGU6ICdzZWFyY2gnLFxuICAgICAgY2xhc3NOYW1lOiAnbXctaW5wdXQnLFxuICAgICAgYXV0b2NvbXBsZXRlOiAnb2ZmJyxcbiAgICAgIGF1dG9jb3JyZWN0OiAnb2ZmJyxcbiAgICAgIGF1dG9jYXBpdGFsaXplOiAnb2ZmJyxcbiAgICAgIHNwZWxsY2hlY2s6IGZhbHNlLFxuICAgICAgJ3JvbGUnOiAnY29tYm9ib3gnLFxuICAgICAgJ2FyaWEtZXhwYW5kZWQnOiAnZmFsc2UnLFxuICAgICAgJ2FyaWEtaGFzcG9wdXAnOiAnbGlzdGJveCcsXG4gICAgICAnYXJpYS1hdXRvY29tcGxldGUnOiAnbGlzdCcsXG4gICAgICAnYXJpYS1jb250cm9scyc6ICdtdy1saXN0Ym94JyxcbiAgICAgICdhcmlhLWFjdGl2ZWRlc2NlbmRhbnQnOiAnJyxcbiAgICB9KTtcbiAgICBzZXRUZXh0KGlucHV0LCAnJyk7XG4gICAgaW5wdXQucGxhY2Vob2xkZXIgPSB0aGlzLl9jb25maWcucGxhY2Vob2xkZXI7XG4gICAgaW5wdXQuc2V0QXR0cmlidXRlKCdlbnRlcmtleWhpbnQnLCAnc2VhcmNoJyk7XG5cbiAgICAvLyBDbGVhciBidXR0b24gKGhpZGRlbiB1bnRpbCB0ZXh0KVxuICAgIGNvbnN0IGNsZWFyQnRuID0gY3JlYXRlRWwoJ2J1dHRvbicsIHtcbiAgICAgIGNsYXNzTmFtZTogJ213LWNsZWFyLWJ0biBtdy1oaWRkZW4nLFxuICAgICAgdHlwZTogJ2J1dHRvbicsXG4gICAgICAnYXJpYS1sYWJlbCc6ICdDbGVhciBzZWFyY2gnLFxuICAgIH0pO1xuICAgIGNsZWFyQnRuLmlubmVySFRNTCA9ICc8c3ZnIHZpZXdCb3g9XCIwIDAgMjQgMjRcIiBhcmlhLWhpZGRlbj1cInRydWVcIj48cGF0aCBkPVwiTTE4IDZMNiAxOE02IDZsMTIgMTJcIiBzdHJva2U9XCJjdXJyZW50Q29sb3JcIiBzdHJva2Utd2lkdGg9XCIyXCIgc3Ryb2tlLWxpbmVjYXA9XCJyb3VuZFwiLz48L3N2Zz4nO1xuXG4gICAgaW5wdXRSb3cuYXBwZW5kQ2hpbGQobGFiZWwpO1xuICAgIGlucHV0Um93LmFwcGVuZENoaWxkKHNlYXJjaEljb24pO1xuICAgIGlucHV0Um93LmFwcGVuZENoaWxkKGlucHV0KTtcbiAgICBpbnB1dFJvdy5hcHBlbmRDaGlsZChjbGVhckJ0bik7XG5cbiAgICAvLyAtLS0gU3RhdHVzIChBUklBIGxpdmUgcmVnaW9uKSAtLS1cbiAgICBjb25zdCBzdGF0dXMgPSBjcmVhdGVFbCgnZGl2Jywge1xuICAgICAgY2xhc3NOYW1lOiAnbXctc3RhdHVzJyxcbiAgICAgIHJvbGU6ICdzdGF0dXMnLFxuICAgICAgJ2FyaWEtbGl2ZSc6ICdwb2xpdGUnLFxuICAgICAgJ2FyaWEtYXRvbWljJzogJ3RydWUnLFxuICAgIH0pO1xuXG4gICAgLy8gLS0tIERyb3Bkb3duIGxpc3Rib3ggLS0tXG4gICAgY29uc3QgZHJvcGRvd24gPSBjcmVhdGVFbCgnZGl2Jywge1xuICAgICAgaWQ6ICdtdy1saXN0Ym94JyxcbiAgICAgIGNsYXNzTmFtZTogJ213LWRyb3Bkb3duJyxcbiAgICAgIHJvbGU6ICdsaXN0Ym94JyxcbiAgICAgICdhcmlhLWxhYmVsJzogJ1NlYXJjaCByZXN1bHRzJyxcbiAgICB9KTtcbiAgICBkcm9wZG93bi5zZXRBdHRyaWJ1dGUoJ2FyaWEtaGlkZGVuJywgJ3RydWUnKTtcblxuICAgIHdyYXBwZXIuYXBwZW5kQ2hpbGQoaW5wdXRSb3cpO1xuICAgIHdyYXBwZXIuYXBwZW5kQ2hpbGQoc3RhdHVzKTtcbiAgICB3cmFwcGVyLmFwcGVuZENoaWxkKGRyb3Bkb3duKTtcbiAgICBzaGFkb3cuYXBwZW5kQ2hpbGQod3JhcHBlcik7XG5cbiAgICB0aGlzLl9lbHMgPSB7IGlucHV0LCBjbGVhckJ0biwgc3RhdHVzLCBkcm9wZG93biwgd3JhcHBlciB9O1xuICB9XG5cbiAgX21ha2VTZWFyY2hJY29uKCkge1xuICAgIGNvbnN0IGljb24gPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50TlMoJ2h0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnJywgJ3N2ZycpO1xuICAgIGljb24uc2V0QXR0cmlidXRlKCdjbGFzcycsICdtdy1zZWFyY2gtaWNvbicpO1xuICAgIGljb24uc2V0QXR0cmlidXRlKCd2aWV3Qm94JywgJzAgMCAyNCAyNCcpO1xuICAgIGljb24uc2V0QXR0cmlidXRlKCdhcmlhLWhpZGRlbicsICd0cnVlJyk7XG4gICAgaWNvbi5zZXRBdHRyaWJ1dGUoJ2ZvY3VzYWJsZScsICdmYWxzZScpO1xuICAgIGNvbnN0IHBhdGggPSBkb2N1bWVudC5jcmVhdGVFbGVtZW50TlMoJ2h0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnJywgJ3BhdGgnKTtcbiAgICBwYXRoLnNldEF0dHJpYnV0ZSgnZCcsICdNMjEgMjFsLTYtNm0yLTVhNyA3IDAgMTEtMTQgMCA3IDcgMCAwMTE0IDB6Jyk7XG4gICAgcGF0aC5zZXRBdHRyaWJ1dGUoJ3N0cm9rZScsICdjdXJyZW50Q29sb3InKTtcbiAgICBwYXRoLnNldEF0dHJpYnV0ZSgnc3Ryb2tlLXdpZHRoJywgJzInKTtcbiAgICBwYXRoLnNldEF0dHJpYnV0ZSgnc3Ryb2tlLWxpbmVjYXAnLCAncm91bmQnKTtcbiAgICBwYXRoLnNldEF0dHJpYnV0ZSgnZmlsbCcsICdub25lJyk7XG4gICAgaWNvbi5hcHBlbmRDaGlsZChwYXRoKTtcbiAgICByZXR1cm4gaWNvbjtcbiAgfVxuXG4gIC8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuICAvLyBSZW1vdGUgdGhlbWVcbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIF9hcHBseVJlbW90ZVRoZW1lKGNmZykge1xuICAgIGNvbnN0IG92ZXJyaWRlcyA9IFtdO1xuICAgIGNvbnN0IHNhZmVDb2xvciA9ICh2KSA9PiAodHlwZW9mIHYgPT09ICdzdHJpbmcnICYmIC9eI1swLTlhLWZBLUZdezMsOH0kfF5yZ2JhP1xcKHxeaHNsLy50ZXN0KHYpKSA/IHYgOiBudWxsO1xuICAgIGNvbnN0IHNhZmVGb250RmFtaWx5ID0gKHYpID0+ICh0eXBlb2YgdiA9PT0gJ3N0cmluZycgJiYgdi5sZW5ndGggPCAyMDApID8gdiA6IG51bGw7XG5cbiAgICBjb25zdCBjID0gc2FmZUNvbG9yKGNmZy53aWRnZXRfcHJpbWFyeV9jb2xvcik7XG4gICAgaWYgKGMpIG92ZXJyaWRlcy5wdXNoKGAtLW1lcmN1cnktYWNjZW50OiAke2N9O2ApO1xuXG4gICAgY29uc3QgZiA9IHNhZmVGb250RmFtaWx5KGNmZy53aWRnZXRfZm9udF9mYW1pbHkpO1xuICAgIGlmIChmKSBvdmVycmlkZXMucHVzaChgLS1tZXJjdXJ5LWZvbnQ6ICR7Zn0sIHN5c3RlbS11aSwgc2Fucy1zZXJpZjtgKTtcblxuICAgIGNvbnN0IHBoID0gdHlwZW9mIGNmZy53aWRnZXRfcGxhY2Vob2xkZXIgPT09ICdzdHJpbmcnID8gY2ZnLndpZGdldF9wbGFjZWhvbGRlciA6IG51bGw7XG4gICAgaWYgKHBoICYmIHRoaXMuX2Vscy5pbnB1dCkgdGhpcy5fZWxzLmlucHV0LnBsYWNlaG9sZGVyID0gcGguc2xpY2UoMCwgMTAwKTtcblxuICAgIGlmIChvdmVycmlkZXMubGVuZ3RoKSB7XG4gICAgICBjb25zdCBleHRyYSA9IGRvY3VtZW50LmNyZWF0ZUVsZW1lbnQoJ3N0eWxlJyk7XG4gICAgICBleHRyYS50ZXh0Q29udGVudCA9IGA6aG9zdCB7ICR7b3ZlcnJpZGVzLmpvaW4oJyAnKX0gfWA7XG4gICAgICB0aGlzLl9zaGFkb3cuYXBwZW5kQ2hpbGQoZXh0cmEpO1xuICAgIH1cbiAgfVxuXG4gIC8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuICAvLyBFdmVudCBiaW5kaW5nIChhbGwgdHJhY2tlZCBmb3IgY2xlYW51cClcbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIF9vbih0YXJnZXQsIHR5cGUsIGZuLCBvcHRzKSB7XG4gICAgdGFyZ2V0LmFkZEV2ZW50TGlzdGVuZXIodHlwZSwgZm4sIG9wdHMpO1xuICAgIHRoaXMuX2xpc3RlbmVycy5wdXNoKHsgdGFyZ2V0LCB0eXBlLCBmbiwgb3B0cyB9KTtcbiAgfVxuXG4gIF9iaW5kRXZlbnRzKCkge1xuICAgIGNvbnN0IHsgaW5wdXQsIGNsZWFyQnRuLCBkcm9wZG93biB9ID0gdGhpcy5fZWxzO1xuXG4gICAgLy8gSW5wdXQgdHlwaW5nIFx1MjE5MiBkZWJvdW5jZWQgc2VhcmNoXG4gICAgdGhpcy5fb24oaW5wdXQsICdpbnB1dCcsICgpID0+IHtcbiAgICAgIGNvbnN0IHZhbCA9IGlucHV0LnZhbHVlO1xuICAgICAgaWYgKHZhbCAhPT0gdGhpcy5fc3RhdGUucXVlcnkpIHtcbiAgICAgICAgdGhpcy5fc3RhdGUucXVlcnkgPSB2YWw7XG4gICAgICAgIHRoaXMuX3N0YXRlLnNlbGVjdGVkSW5kZXggPSAtMTtcbiAgICAgICAgaWYgKCF2YWwudHJpbSgpIHx8IHZhbC50cmltKCkubGVuZ3RoIDwgKHRoaXMuX2NvbmZpZy5taW5MZW5ndGggfHwgMikpIHtcbiAgICAgICAgICB0aGlzLl9jbG9zZURyb3Bkb3duKCk7XG4gICAgICAgICAgdGhpcy5fY2xlYXJTdGF0dXMoKTtcbiAgICAgICAgICB0aGlzLl91cGRhdGVDbGVhckJ0bigpO1xuICAgICAgICAgIHJldHVybjtcbiAgICAgICAgfVxuICAgICAgICB0aGlzLl91cGRhdGVDbGVhckJ0bigpO1xuICAgICAgICB0aGlzLl9kZWJvdW5jZVNlYXJjaCh2YWwudHJpbSgpKTtcbiAgICAgIH1cbiAgICB9KTtcblxuICAgIC8vIEtleWJvYXJkIG5hdmlnYXRpb24gKG5vdCBkZWJvdW5jZWQpXG4gICAgdGhpcy5fb24oaW5wdXQsICdrZXlkb3duJywgKGUpID0+IHRoaXMuX2hhbmRsZUtleWRvd24oZSkpO1xuXG4gICAgLy8gRm9jdXMgXHUyMTkyIHJlb3BlbiBpZiBxdWVyeSBleGlzdHNcbiAgICB0aGlzLl9vbihpbnB1dCwgJ2ZvY3VzJywgKCkgPT4ge1xuICAgICAgaWYgKHRoaXMuX3N0YXRlLnF1ZXJ5LnRyaW0oKS5sZW5ndGggPj0gKHRoaXMuX2NvbmZpZy5taW5MZW5ndGggfHwgMikgJiYgdGhpcy5fc3RhdGUucmVzdWx0cy5sZW5ndGgpIHtcbiAgICAgICAgdGhpcy5fb3BlbkRyb3Bkb3duKCk7XG4gICAgICB9XG4gICAgfSk7XG5cbiAgICAvLyBDbGVhciBidXR0b25cbiAgICB0aGlzLl9vbihjbGVhckJ0biwgJ2NsaWNrJywgKCkgPT4ge1xuICAgICAgaW5wdXQudmFsdWUgPSAnJztcbiAgICAgIHRoaXMuX3N0YXRlLnF1ZXJ5ID0gJyc7XG4gICAgICB0aGlzLl9zdGF0ZS5yZXN1bHRzID0gW107XG4gICAgICB0aGlzLl9zdGF0ZS5zZWxlY3RlZEluZGV4ID0gLTE7XG4gICAgICB0aGlzLl9jbG9zZURyb3Bkb3duKCk7XG4gICAgICB0aGlzLl9jbGVhclN0YXR1cygpO1xuICAgICAgdGhpcy5fdXBkYXRlQ2xlYXJCdG4oKTtcbiAgICAgIGlucHV0LmZvY3VzKCk7XG4gICAgfSk7XG5cbiAgICAvLyBDbG9zZSBvbiBvdXRzaWRlIGNsaWNrIChkb2N1bWVudC1sZXZlbCwgd2l0aCBjbGVhbnVwIHBhdGgpXG4gICAgY29uc3Qgb3V0c2lkZUNsaWNrID0gKGUpID0+IHtcbiAgICAgIGlmICghdGhpcy5jb250YWlucyhlLnRhcmdldCkgJiYgIXRoaXMuX3NoYWRvdy5jb250YWlucyhlLnRhcmdldCkpIHtcbiAgICAgICAgdGhpcy5fY2xvc2VEcm9wZG93bigpO1xuICAgICAgfVxuICAgIH07XG4gICAgdGhpcy5fb24oZG9jdW1lbnQsICdjbGljaycsIG91dHNpZGVDbGljaywgdHJ1ZSk7XG5cbiAgICAvLyBLZXlib2FyZDogRXNjYXBlIGdsb2JhbGx5IHdoZW4gb3BlblxuICAgIGNvbnN0IGdsb2JhbEVzYyA9IChlKSA9PiB7XG4gICAgICBpZiAoZS5rZXkgPT09ICdFc2NhcGUnICYmIHRoaXMuX3N0YXRlLmlzT3Blbikge1xuICAgICAgICB0aGlzLl9jbG9zZURyb3Bkb3duKCk7XG4gICAgICAgIGlucHV0LmZvY3VzKCk7XG4gICAgICB9XG4gICAgfTtcbiAgICB0aGlzLl9vbihkb2N1bWVudCwgJ2tleWRvd24nLCBnbG9iYWxFc2MsIHRydWUpO1xuXG4gICAgLy8gRHJvcGRvd24gY2xpY2sgZGVsZWdhdGlvblxuICAgIHRoaXMuX29uKGRyb3Bkb3duLCAnY2xpY2snLCAoZSkgPT4ge1xuICAgICAgY29uc3QgaXRlbSA9IGUudGFyZ2V0LmNsb3Nlc3QoJ1tyb2xlPVwib3B0aW9uXCJdJyk7XG4gICAgICBpZiAoaXRlbSkge1xuICAgICAgICBjb25zdCBpZHggPSBwYXJzZUludChpdGVtLmRhdGFzZXQuaW5kZXgsIDEwKTtcbiAgICAgICAgaWYgKE51bWJlci5pc0Zpbml0ZShpZHgpKSB0aGlzLl9zZWxlY3RSZXN1bHQoaWR4KTtcbiAgICAgIH1cbiAgICB9KTtcblxuICAgIC8vIFByZXZlbnQgZm9jdXMgbGVhdmluZyBzaGFkb3cgKFRhYiBiZWhhdmlvcjogZG9uJ3QgdHJhcClcbiAgICB0aGlzLl9vbihkcm9wZG93biwgJ21vdXNlZG93bicsIChlKSA9PiB7XG4gICAgICAvLyBQcmV2ZW50IGlucHV0IGJsdXIgd2hlbiBjbGlja2luZyByZXN1bHRzXG4gICAgICBlLnByZXZlbnREZWZhdWx0KCk7XG4gICAgfSk7XG4gIH1cblxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgLy8gS2V5Ym9hcmQgaGFuZGxlclxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgX2hhbmRsZUtleWRvd24oZSkge1xuICAgIGNvbnN0IHsgcmVzdWx0cywgc2VsZWN0ZWRJbmRleCwgaXNPcGVuIH0gPSB0aGlzLl9zdGF0ZTtcbiAgICBjb25zdCBjb3VudCA9IHJlc3VsdHMubGVuZ3RoO1xuXG4gICAgc3dpdGNoIChlLmtleSkge1xuICAgICAgY2FzZSAnQXJyb3dEb3duJzpcbiAgICAgICAgaWYgKCFpc09wZW4gJiYgY291bnQpIHsgdGhpcy5fb3BlbkRyb3Bkb3duKCk7IHJldHVybjsgfVxuICAgICAgICBpZiAoIWNvdW50KSByZXR1cm47XG4gICAgICAgIGUucHJldmVudERlZmF1bHQoKTtcbiAgICAgICAgdGhpcy5fc2V0U2VsZWN0ZWQoc2VsZWN0ZWRJbmRleCA8IGNvdW50IC0gMSA/IHNlbGVjdGVkSW5kZXggKyAxIDogMCk7XG4gICAgICAgIGJyZWFrO1xuXG4gICAgICBjYXNlICdBcnJvd1VwJzpcbiAgICAgICAgaWYgKCFpc09wZW4gfHwgIWNvdW50KSByZXR1cm47XG4gICAgICAgIGUucHJldmVudERlZmF1bHQoKTtcbiAgICAgICAgdGhpcy5fc2V0U2VsZWN0ZWQoc2VsZWN0ZWRJbmRleCA+IDAgPyBzZWxlY3RlZEluZGV4IC0gMSA6IGNvdW50IC0gMSk7XG4gICAgICAgIGJyZWFrO1xuXG4gICAgICBjYXNlICdFbnRlcic6XG4gICAgICAgIGUucHJldmVudERlZmF1bHQoKTtcbiAgICAgICAgaWYgKGlzT3BlbiAmJiBzZWxlY3RlZEluZGV4ID49IDAgJiYgc2VsZWN0ZWRJbmRleCA8IGNvdW50KSB7XG4gICAgICAgICAgdGhpcy5fc2VsZWN0UmVzdWx0KHNlbGVjdGVkSW5kZXgpO1xuICAgICAgICB9IGVsc2UgaWYgKHRoaXMuX3N0YXRlLnF1ZXJ5LnRyaW0oKS5sZW5ndGggPj0gKHRoaXMuX2NvbmZpZy5taW5MZW5ndGggfHwgMikpIHtcbiAgICAgICAgICAvLyBFeGVjdXRlIHNlYXJjaCBpbW1lZGlhdGVseSAoYnlwYXNzIGRlYm91bmNlKVxuICAgICAgICAgIHRoaXMuX2V4ZWN1dGVTZWFyY2godGhpcy5fc3RhdGUucXVlcnkudHJpbSgpKTtcbiAgICAgICAgfVxuICAgICAgICBicmVhaztcblxuICAgICAgY2FzZSAnVGFiJzpcbiAgICAgICAgLy8gRG9uJ3QgdHJhcDsgbGV0IG5hdHVyYWwgdGFiIG9yZGVyIHByb2NlZWQsIGp1c3QgY2xvc2UgZHJvcGRvd25cbiAgICAgICAgaWYgKGlzT3BlbikgdGhpcy5fY2xvc2VEcm9wZG93bigpO1xuICAgICAgICBicmVhaztcblxuICAgICAgLy8gRXNjYXBlIGhhbmRsZWQgYXQgZG9jdW1lbnQgbGV2ZWxcbiAgICB9XG4gIH1cblxuICBfc2V0U2VsZWN0ZWQoaWR4KSB7XG4gICAgdGhpcy5fc3RhdGUuc2VsZWN0ZWRJbmRleCA9IGlkeDtcbiAgICB0aGlzLl91cGRhdGVTZWxlY3Rpb25ET00oKTtcblxuICAgIGNvbnN0IHsgaW5wdXQgfSA9IHRoaXMuX2VscztcbiAgICBjb25zdCBpdGVtSWQgPSBpZHggPj0gMCA/IGBtdy1vcHQtJHtpZHh9YCA6ICcnO1xuICAgIGlucHV0LnNldEF0dHJpYnV0ZSgnYXJpYS1hY3RpdmVkZXNjZW5kYW50JywgaXRlbUlkKTtcbiAgfVxuXG4gIF91cGRhdGVTZWxlY3Rpb25ET00oKSB7XG4gICAgY29uc3QgeyBkcm9wZG93biB9ID0gdGhpcy5fZWxzO1xuICAgIGNvbnN0IGl0ZW1zID0gZHJvcGRvd24ucXVlcnlTZWxlY3RvckFsbCgnW3JvbGU9XCJvcHRpb25cIl0nKTtcbiAgICBpdGVtcy5mb3JFYWNoKChlbCwgaSkgPT4ge1xuICAgICAgY29uc3Qgc2VsZWN0ZWQgPSBpID09PSB0aGlzLl9zdGF0ZS5zZWxlY3RlZEluZGV4O1xuICAgICAgZWwuc2V0QXR0cmlidXRlKCdhcmlhLXNlbGVjdGVkJywgc2VsZWN0ZWQgPyAndHJ1ZScgOiAnZmFsc2UnKTtcbiAgICAgIGVsLmNsYXNzTGlzdC50b2dnbGUoJ213LXNlbGVjdGVkJywgc2VsZWN0ZWQpO1xuICAgICAgaWYgKHNlbGVjdGVkKSB7XG4gICAgICAgIGVsLnNjcm9sbEludG9WaWV3KHsgYmxvY2s6ICduZWFyZXN0JywgYmVoYXZpb3I6ICdzbW9vdGgnIH0pO1xuICAgICAgfVxuICAgIH0pO1xuICB9XG5cbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIC8vIFNlYXJjaCBleGVjdXRpb25cbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIGFzeW5jIF9leGVjdXRlU2VhcmNoKHF1ZXJ5KSB7XG4gICAgaWYgKCFxdWVyeSB8fCBxdWVyeS5sZW5ndGggPCAodGhpcy5fY29uZmlnLm1pbkxlbmd0aCB8fCAyKSkgcmV0dXJuO1xuXG4gICAgdGhpcy5fc3RhdGUuaXNMb2FkaW5nID0gdHJ1ZTtcbiAgICB0aGlzLl9zdGF0ZS5lcnJvciA9IG51bGw7XG4gICAgdGhpcy5fc3RhdGUuc2VsZWN0ZWRJbmRleCA9IC0xO1xuICAgIHRoaXMuX3JlbmRlckxvYWRpbmcoKTtcbiAgICB0aGlzLl9vcGVuRHJvcGRvd24oKTtcbiAgICB0aGlzLl9hbm5vdW5jZVN0YXR1cygnU2VhcmNoaW5nXHUyMDI2Jyk7XG4gICAgdGhpcy5fc2VuZFRlbGVtZXRyeSh7IGV2ZW50OiAnc2VhcmNoX3JlcXVlc3RlZCcsIHF1ZXJ5IH0pO1xuXG4gICAgdHJ5IHtcbiAgICAgIGNvbnN0IHsgcmVzdWx0cywgc2VhcmNoSWQgfSA9IGF3YWl0IHRoaXMuX2FwaS5zZWFyY2gocXVlcnksIHRoaXMuX2NvbmZpZy5saW1pdCB8fCA4KTtcblxuICAgICAgLy8gUmFjZSBwcm90ZWN0aW9uOiBpZ25vcmUgaWYgcXVlcnkgY2hhbmdlZCB3aGlsZSBhd2FpdGluZ1xuICAgICAgaWYgKHF1ZXJ5ICE9PSB0aGlzLl9zdGF0ZS5xdWVyeS50cmltKCkpIHJldHVybjtcblxuICAgICAgdGhpcy5fc3RhdGUuaXNMb2FkaW5nID0gZmFsc2U7XG4gICAgICB0aGlzLl9zdGF0ZS5yZXN1bHRzID0gcmVzdWx0cy5maWx0ZXIoQm9vbGVhbik7XG4gICAgICB0aGlzLl9zdGF0ZS5zZWFyY2hJZCA9IHNlYXJjaElkO1xuICAgICAgdGhpcy5fcmVuZGVyUmVzdWx0cygpO1xuXG4gICAgICBjb25zdCBjb3VudCA9IHRoaXMuX3N0YXRlLnJlc3VsdHMubGVuZ3RoO1xuICAgICAgaWYgKGNvdW50ID09PSAwKSB7XG4gICAgICAgIHRoaXMuX2Fubm91bmNlU3RhdHVzKGBObyByZXN1bHRzIGZvciBcIiR7cXVlcnl9XCJgKTtcbiAgICAgICAgdGhpcy5fc2VuZFRlbGVtZXRyeSh7IGV2ZW50OiAnc2VhcmNoX25vX3Jlc3VsdHMnLCBxdWVyeSB9KTtcbiAgICAgIH0gZWxzZSB7XG4gICAgICAgIHRoaXMuX2Fubm91bmNlU3RhdHVzKGAke2NvdW50fSByZXN1bHQke2NvdW50ID09PSAxID8gJycgOiAncyd9IGZvdW5kYCk7XG4gICAgICAgIHRoaXMuX3NlbmRUZWxlbWV0cnkoeyBldmVudDogJ3NlYXJjaF9yZXN1bHRzX3JlY2VpdmVkJywgcXVlcnksIG1ldGFkYXRhOiB7IGNvdW50IH0gfSk7XG4gICAgICB9XG4gICAgfSBjYXRjaCAoZXJyKSB7XG4gICAgICBpZiAoZXJyIGluc3RhbmNlb2YgTWVyY3VyeUFwaUVycm9yICYmIGVyci50eXBlID09PSBBcGlFcnJvclR5cGUuQUJPUlQpIHJldHVybjtcblxuICAgICAgLy8gT25seSB1cGRhdGUgaWYgcXVlcnkgc3RpbGwgbWF0Y2hlc1xuICAgICAgaWYgKHF1ZXJ5ICE9PSB0aGlzLl9zdGF0ZS5xdWVyeS50cmltKCkpIHJldHVybjtcblxuICAgICAgdGhpcy5fc3RhdGUuaXNMb2FkaW5nID0gZmFsc2U7XG4gICAgICB0aGlzLl9zdGF0ZS5lcnJvciA9IGVyciBpbnN0YW5jZW9mIE1lcmN1cnlBcGlFcnJvciA/IGVyci5tZXNzYWdlIDogJ1NlYXJjaCB1bmF2YWlsYWJsZS4gUGxlYXNlIHRyeSBhZ2Fpbi4nO1xuICAgICAgdGhpcy5fcmVuZGVyRXJyb3IodGhpcy5fc3RhdGUuZXJyb3IpO1xuICAgICAgdGhpcy5fYW5ub3VuY2VTdGF0dXModGhpcy5fc3RhdGUuZXJyb3IpO1xuICAgIH1cbiAgfVxuXG4gIC8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuICAvLyBSZXN1bHQgc2VsZWN0aW9uXG4gIC8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuICBfc2VsZWN0UmVzdWx0KGlkeCkge1xuICAgIGNvbnN0IGl0ZW0gPSB0aGlzLl9zdGF0ZS5yZXN1bHRzW2lkeF07XG4gICAgaWYgKCFpdGVtKSByZXR1cm47XG5cbiAgICAvLyBEZWR1cDogaWdub3JlIGRvdWJsZS1maXJlIHdpdGhpbiAzMDBtcyBvbiBzYW1lIHByb2R1Y3RcbiAgICBjb25zdCBub3cgPSBEYXRlLm5vdygpO1xuICAgIGlmICh0aGlzLl9sYXN0Q2xpY2tlZFByb2R1Y3RJZCA9PT0gaXRlbS5pZCAmJiBub3cgLSB0aGlzLl9sYXN0Q2xpY2tUcyA8IDMwMCkgcmV0dXJuO1xuICAgIHRoaXMuX2xhc3RDbGlja2VkUHJvZHVjdElkID0gaXRlbS5pZDtcbiAgICB0aGlzLl9sYXN0Q2xpY2tUcyA9IG5vdztcblxuICAgIC8vIE5hdmlnYXRlIHRvIHByb2R1Y3QgVVJMIGlmIGF2YWlsYWJsZVxuICAgIGlmIChpdGVtLnByb2R1Y3RVcmwpIHtcbiAgICAgIC8vIEZpcmUgdGVsZW1ldHJ5IGJlZm9yZSBuYXZpZ2F0aW9uXG4gICAgICB0aGlzLl9zZW5kVGVsZW1ldHJ5KHtcbiAgICAgICAgZXZlbnQ6ICdzZWFyY2hfcmVzdWx0X2NsaWNrZWQnLFxuICAgICAgICBxdWVyeTogdGhpcy5fc3RhdGUucXVlcnksXG4gICAgICAgIHByb2R1Y3RJZDogaXRlbS5pZCxcbiAgICAgICAgc2VhcmNoSWQ6IHRoaXMuX3N0YXRlLnNlYXJjaElkLFxuICAgICAgICBzZXNzaW9uSWQ6IHRoaXMuX3Nlc3Npb25JZCxcbiAgICAgICAgcG9zaXRpb246IGlkeCArIDEsXG4gICAgICB9KTtcbiAgICAgIC8vIE5hdmlnYXRlICh0ZWxlbWV0cnkgdXNlcyBzZW5kQmVhY29uIHNvIGl0IGRvZXNuJ3QgYmxvY2spXG4gICAgICB3aW5kb3cubG9jYXRpb24uaHJlZiA9IGl0ZW0ucHJvZHVjdFVybDtcbiAgICB9IGVsc2Uge1xuICAgICAgLy8gRGlzcGF0Y2ggYSBjdXN0b20gZXZlbnQgZm9yIG1lcmNoYW50IHRvIGhhbmRsZVxuICAgICAgdGhpcy5fc2VuZFRlbGVtZXRyeSh7XG4gICAgICAgIGV2ZW50OiAnc2VhcmNoX3Jlc3VsdF9jbGlja2VkJyxcbiAgICAgICAgcXVlcnk6IHRoaXMuX3N0YXRlLnF1ZXJ5LFxuICAgICAgICBwcm9kdWN0SWQ6IGl0ZW0uaWQsXG4gICAgICAgIHNlYXJjaElkOiB0aGlzLl9zdGF0ZS5zZWFyY2hJZCxcbiAgICAgICAgc2Vzc2lvbklkOiB0aGlzLl9zZXNzaW9uSWQsXG4gICAgICAgIHBvc2l0aW9uOiBpZHggKyAxLFxuICAgICAgfSk7XG5cbiAgICAgIHRoaXMuZGlzcGF0Y2hFdmVudChuZXcgQ3VzdG9tRXZlbnQoJ21lcmN1cnk6cmVzdWx0LXNlbGVjdGVkJywge1xuICAgICAgICBidWJibGVzOiB0cnVlLFxuICAgICAgICBjb21wb3NlZDogdHJ1ZSwgLy8gY3Jvc3NlcyBzaGFkb3cgYm91bmRhcnlcbiAgICAgICAgZGV0YWlsOiB7IHByb2R1Y3Q6IGl0ZW0sIHF1ZXJ5OiB0aGlzLl9zdGF0ZS5xdWVyeSwgcG9zaXRpb246IGlkeCArIDEgfSxcbiAgICAgIH0pKTtcbiAgICB9XG5cbiAgICB0aGlzLl9jbG9zZURyb3Bkb3duKCk7XG4gIH1cblxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgLy8gRHJvcGRvd24gb3Blbi9jbG9zZVxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgX29wZW5Ecm9wZG93bigpIHtcbiAgICBpZiAodGhpcy5fc3RhdGUuaXNPcGVuKSByZXR1cm47XG4gICAgdGhpcy5fc3RhdGUuaXNPcGVuID0gdHJ1ZTtcbiAgICBjb25zdCB7IGRyb3Bkb3duLCBpbnB1dCB9ID0gdGhpcy5fZWxzO1xuICAgIGRyb3Bkb3duLmNsYXNzTGlzdC5hZGQoJ213LW9wZW4nKTtcbiAgICBkcm9wZG93bi5zZXRBdHRyaWJ1dGUoJ2FyaWEtaGlkZGVuJywgJ2ZhbHNlJyk7XG4gICAgaW5wdXQuc2V0QXR0cmlidXRlKCdhcmlhLWV4cGFuZGVkJywgJ3RydWUnKTtcbiAgICB0aGlzLl9wb3NpdGlvbkRyb3Bkb3duKCk7XG4gIH1cblxuICBfY2xvc2VEcm9wZG93bigpIHtcbiAgICB0aGlzLl9zdGF0ZS5pc09wZW4gPSBmYWxzZTtcbiAgICB0aGlzLl9zdGF0ZS5zZWxlY3RlZEluZGV4ID0gLTE7XG4gICAgY29uc3QgeyBkcm9wZG93biwgaW5wdXQgfSA9IHRoaXMuX2VscztcbiAgICBkcm9wZG93bi5jbGFzc0xpc3QucmVtb3ZlKCdtdy1vcGVuJyk7XG4gICAgZHJvcGRvd24uc2V0QXR0cmlidXRlKCdhcmlhLWhpZGRlbicsICd0cnVlJyk7XG4gICAgaW5wdXQuc2V0QXR0cmlidXRlKCdhcmlhLWV4cGFuZGVkJywgJ2ZhbHNlJyk7XG4gICAgaW5wdXQuc2V0QXR0cmlidXRlKCdhcmlhLWFjdGl2ZWRlc2NlbmRhbnQnLCAnJyk7XG4gIH1cblxuICAvKipcbiAgICogRmxpcCBkcm9wZG93biBhYm92ZSBpbnB1dCBpZiBub3QgZW5vdWdoIHNwYWNlIGJlbG93LlxuICAgKi9cbiAgX3Bvc2l0aW9uRHJvcGRvd24oKSB7XG4gICAgY29uc3QgeyBkcm9wZG93biwgd3JhcHBlciB9ID0gdGhpcy5fZWxzO1xuICAgIGNvbnN0IHJlY3QgPSB3cmFwcGVyLmdldEJvdW5kaW5nQ2xpZW50UmVjdCgpO1xuICAgIGNvbnN0IHNwYWNlQmVsb3cgPSB3aW5kb3cuaW5uZXJIZWlnaHQgLSByZWN0LmJvdHRvbTtcbiAgICBjb25zdCBzcGFjZUFib3ZlID0gcmVjdC50b3A7XG5cbiAgICBpZiAoc3BhY2VCZWxvdyA8IDIwMCAmJiBzcGFjZUFib3ZlID4gc3BhY2VCZWxvdykge1xuICAgICAgZHJvcGRvd24uY2xhc3NMaXN0LmFkZCgnbXctZmxpcCcpO1xuICAgIH0gZWxzZSB7XG4gICAgICBkcm9wZG93bi5jbGFzc0xpc3QucmVtb3ZlKCdtdy1mbGlwJyk7XG4gICAgfVxuICB9XG5cbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIC8vIFJlbmRlcmluZyBoZWxwZXJzIChhbGwgc2FmZSBcdTIwMTMgbm8gaW5uZXJIVE1MIHdpdGggdW50cnVzdGVkIGRhdGEpXG4gIC8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuICBfcmVuZGVyTG9hZGluZygpIHtcbiAgICBjb25zdCB7IGRyb3Bkb3duIH0gPSB0aGlzLl9lbHM7XG4gICAgZHJvcGRvd24uaW5uZXJIVE1MID0gJyc7XG5cbiAgICBjb25zdCBtc2cgPSBjcmVhdGVFbCgnZGl2JywgeyBjbGFzc05hbWU6ICdtdy1zdGF0ZS1tc2cnLCAnYXJpYS1idXN5JzogJ3RydWUnIH0pO1xuICAgIGNvbnN0IHNwaW5uZXIgPSBjcmVhdGVFbCgnc3BhbicsIHsgY2xhc3NOYW1lOiAnbXctc3Bpbm5lcicsICdhcmlhLWhpZGRlbic6ICd0cnVlJyB9KTtcbiAgICBtc2cuYXBwZW5kQ2hpbGQoc3Bpbm5lcik7XG4gICAgbXNnLmFwcGVuZENoaWxkKGRvY3VtZW50LmNyZWF0ZVRleHROb2RlKCcgU2VhcmNoaW5nXHUyMDI2JykpO1xuICAgIGRyb3Bkb3duLmFwcGVuZENoaWxkKG1zZyk7XG4gICAgdGhpcy5fb3BlbkRyb3Bkb3duKCk7XG4gIH1cblxuICBfcmVuZGVyRXJyb3Ioc2FmZU1zZykge1xuICAgIGNvbnN0IHsgZHJvcGRvd24gfSA9IHRoaXMuX2VscztcbiAgICBkcm9wZG93bi5pbm5lckhUTUwgPSAnJztcbiAgICBjb25zdCBtc2cgPSBjcmVhdGVFbCgnZGl2JywgeyBjbGFzc05hbWU6ICdtdy1zdGF0ZS1tc2cgbXctc3RhdGUtZXJyb3InIH0sIHNhZmVNc2cpO1xuICAgIGRyb3Bkb3duLmFwcGVuZENoaWxkKG1zZyk7XG4gIH1cblxuICBfcmVuZGVyUmVzdWx0cygpIHtcbiAgICBjb25zdCB7IGRyb3Bkb3duIH0gPSB0aGlzLl9lbHM7XG4gICAgY29uc3QgeyByZXN1bHRzIH0gPSB0aGlzLl9zdGF0ZTtcbiAgICBkcm9wZG93bi5pbm5lckhUTUwgPSAnJztcblxuICAgIGlmIChyZXN1bHRzLmxlbmd0aCA9PT0gMCkge1xuICAgICAgY29uc3QgbXNnID0gY3JlYXRlRWwoJ2RpdicsIHsgY2xhc3NOYW1lOiAnbXctc3RhdGUtbXNnIG13LXN0YXRlLWVtcHR5JyB9KTtcbiAgICAgIHNldFRleHQobXNnLCAnTm8gcHJvZHVjdHMgZm91bmQgZm9yIFwiJyk7XG4gICAgICBjb25zdCBxID0gY3JlYXRlRWwoJ3N0cm9uZycpO1xuICAgICAgc2V0VGV4dChxLCB0aGlzLl9zdGF0ZS5xdWVyeSk7XG4gICAgICBtc2cuYXBwZW5kQ2hpbGQocSk7XG4gICAgICBtc2cuYXBwZW5kQ2hpbGQoZG9jdW1lbnQuY3JlYXRlVGV4dE5vZGUoJ1wiJykpO1xuXG4gICAgICBjb25zdCBoaW50ID0gY3JlYXRlRWwoJ3AnLCB7IGNsYXNzTmFtZTogJ213LWVtcHR5LWhpbnQnIH0sICdUcnkgZGlmZmVyZW50IGtleXdvcmRzIG9yIGJyb3dzZSBhbGwgY2F0ZWdvcmllcy4nKTtcbiAgICAgIG1zZy5hcHBlbmRDaGlsZChoaW50KTtcbiAgICAgIGRyb3Bkb3duLmFwcGVuZENoaWxkKG1zZyk7XG4gICAgICByZXR1cm47XG4gICAgfVxuXG4gICAgcmVzdWx0cy5mb3JFYWNoKChpdGVtLCBpZHgpID0+IHtcbiAgICAgIGNvbnN0IG9wdGlvbiA9IHRoaXMuX2J1aWxkUmVzdWx0SXRlbShpdGVtLCBpZHgpO1xuICAgICAgZHJvcGRvd24uYXBwZW5kQ2hpbGQob3B0aW9uKTtcbiAgICB9KTtcblxuICAgIHRoaXMuX3VwZGF0ZVNlbGVjdGlvbkRPTSgpO1xuICB9XG5cbiAgX2J1aWxkUmVzdWx0SXRlbShpdGVtLCBpZHgpIHtcbiAgICAvLyBBbGwgdmFsdWVzIHJlbmRlcmVkIGFzIHRleHQgbm9kZXMgXHUyMDEzIG5ldmVyIGlubmVySFRNTFxuICAgIGNvbnN0IG9wdGlvbiA9IGNyZWF0ZUVsKCdkaXYnLCB7XG4gICAgICBjbGFzc05hbWU6ICdtdy1yZXN1bHQtaXRlbScsXG4gICAgICByb2xlOiAnb3B0aW9uJyxcbiAgICAgIGlkOiBgbXctb3B0LSR7aWR4fWAsXG4gICAgICAnYXJpYS1zZWxlY3RlZCc6ICdmYWxzZScsXG4gICAgfSk7XG4gICAgb3B0aW9uLmRhdGFzZXQuaW5kZXggPSBTdHJpbmcoaWR4KTtcblxuICAgIC8vIEltYWdlIChmaXhlZCBkaW1lbnNpb25zIHRvIHByZXZlbnQgbGF5b3V0IHNoaWZ0KVxuICAgIGNvbnN0IGltZ1dyYXBwZXIgPSBjcmVhdGVFbCgnZGl2JywgeyBjbGFzc05hbWU6ICdtdy1pbWctd3JhcCcgfSk7XG4gICAgaWYgKGl0ZW0uaW1hZ2VVcmwpIHtcbiAgICAgIGNvbnN0IGltZyA9IGNyZWF0ZUVsKCdpbWcnLCB7XG4gICAgICAgIGNsYXNzTmFtZTogJ213LWltZycsXG4gICAgICAgIGFsdDogaXRlbS50aXRsZSB8fCAnUHJvZHVjdCBpbWFnZScsXG4gICAgICAgIGxvYWRpbmc6ICdsYXp5JyxcbiAgICAgICAgZGVjb2Rpbmc6ICdhc3luYycsXG4gICAgICAgIHdpZHRoOiAnNDgnLFxuICAgICAgICBoZWlnaHQ6ICc0OCcsXG4gICAgICB9KTtcbiAgICAgIGltZy5zcmMgPSBpdGVtLmltYWdlVXJsO1xuICAgICAgaW1nLmFkZEV2ZW50TGlzdGVuZXIoJ2Vycm9yJywgKCkgPT4ge1xuICAgICAgICBpbWdXcmFwcGVyLnJlbW92ZUNoaWxkKGltZyk7XG4gICAgICAgIGNvbnN0IHBsYWNlaG9sZGVyID0gY3JlYXRlRWwoJ2RpdicsIHsgY2xhc3NOYW1lOiAnbXctaW1nLXBsYWNlaG9sZGVyJywgJ2FyaWEtaGlkZGVuJzogJ3RydWUnIH0sICdcdUQ4M0RcdURFQ0QnKTtcbiAgICAgICAgaW1nV3JhcHBlci5hcHBlbmRDaGlsZChwbGFjZWhvbGRlcik7XG4gICAgICB9KTtcbiAgICAgIGltZ1dyYXBwZXIuYXBwZW5kQ2hpbGQoaW1nKTtcbiAgICB9IGVsc2Uge1xuICAgICAgY29uc3QgcGxhY2Vob2xkZXIgPSBjcmVhdGVFbCgnZGl2JywgeyBjbGFzc05hbWU6ICdtdy1pbWctcGxhY2Vob2xkZXInLCAnYXJpYS1oaWRkZW4nOiAndHJ1ZScgfSwgJ1x1RDgzRFx1REVDRCcpO1xuICAgICAgaW1nV3JhcHBlci5hcHBlbmRDaGlsZChwbGFjZWhvbGRlcik7XG4gICAgfVxuXG4gICAgLy8gQ29udGVudFxuICAgIGNvbnN0IGNvbnRlbnQgPSBjcmVhdGVFbCgnZGl2JywgeyBjbGFzc05hbWU6ICdtdy1yZXN1bHQtY29udGVudCcgfSk7XG5cbiAgICBjb25zdCB0aXRsZUVsID0gY3JlYXRlRWwoJ2RpdicsIHsgY2xhc3NOYW1lOiAnbXctcmVzdWx0LXRpdGxlJyB9KTtcbiAgICBzZXRUZXh0KHRpdGxlRWwsIGl0ZW0udGl0bGUgfHwgJ1Vua25vd24gUHJvZHVjdCcpO1xuXG4gICAgY29uc3QgbWV0YSA9IGNyZWF0ZUVsKCdkaXYnLCB7IGNsYXNzTmFtZTogJ213LXJlc3VsdC1tZXRhJyB9KTtcbiAgICBpZiAoaXRlbS5icmFuZCB8fCBpdGVtLmNhdGVnb3J5KSB7XG4gICAgICBzZXRUZXh0KG1ldGEsIFtpdGVtLmJyYW5kLCBpdGVtLmNhdGVnb3J5XS5maWx0ZXIoQm9vbGVhbikuam9pbignIFx1MDBCNyAnKSk7XG4gICAgfVxuXG4gICAgY29udGVudC5hcHBlbmRDaGlsZCh0aXRsZUVsKTtcbiAgICBpZiAoaXRlbS5icmFuZCB8fCBpdGVtLmNhdGVnb3J5KSBjb250ZW50LmFwcGVuZENoaWxkKG1ldGEpO1xuXG4gICAgLy8gUHJpY2UgKyBhdmFpbGFiaWxpdHlcbiAgICBjb25zdCByaWdodCA9IGNyZWF0ZUVsKCdkaXYnLCB7IGNsYXNzTmFtZTogJ213LXJlc3VsdC1yaWdodCcgfSk7XG5cbiAgICBpZiAoaXRlbS5wcmljZSAhPT0gbnVsbCAmJiBpdGVtLnByaWNlICE9PSB1bmRlZmluZWQpIHtcbiAgICAgIGNvbnN0IHByaWNlID0gY3JlYXRlRWwoJ2RpdicsIHsgY2xhc3NOYW1lOiAnbXctcmVzdWx0LXByaWNlJyB9KTtcbiAgICAgIHNldFRleHQocHJpY2UsICckJyArIE51bWJlcihpdGVtLnByaWNlKS50b0ZpeGVkKDIpKTtcbiAgICAgIHJpZ2h0LmFwcGVuZENoaWxkKHByaWNlKTtcbiAgICB9XG5cbiAgICBjb25zdCBhdmFpbCA9IGNyZWF0ZUVsKCdkaXYnLCB7XG4gICAgICBjbGFzc05hbWU6ICdtdy1yZXN1bHQtYXZhaWwgJyArIChpdGVtLmluU3RvY2sgPyAnbXctaW5zdG9jaycgOiAnbXctb3V0c3RvY2snKSxcbiAgICB9KTtcbiAgICBzZXRUZXh0KGF2YWlsLCBpdGVtLmluU3RvY2sgPyAnSW4gc3RvY2snIDogJ091dCBvZiBzdG9jaycpO1xuICAgIHJpZ2h0LmFwcGVuZENoaWxkKGF2YWlsKTtcblxuICAgIG9wdGlvbi5hcHBlbmRDaGlsZChpbWdXcmFwcGVyKTtcbiAgICBvcHRpb24uYXBwZW5kQ2hpbGQoY29udGVudCk7XG4gICAgb3B0aW9uLmFwcGVuZENoaWxkKHJpZ2h0KTtcblxuICAgIHJldHVybiBvcHRpb247XG4gIH1cblxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgLy8gU3RhdHVzIChBUklBIGxpdmUgcmVnaW9uKVxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgX2Fubm91bmNlU3RhdHVzKG1zZykge1xuICAgIGNvbnN0IHsgc3RhdHVzIH0gPSB0aGlzLl9lbHM7XG4gICAgaWYgKCFzdGF0dXMpIHJldHVybjtcbiAgICAvLyBDbGVhciBhbmQgcmUtc2V0IHRvIGVuc3VyZSByZS1hbm5vdW5jZW1lbnRcbiAgICBzZXRUZXh0KHN0YXR1cywgJycpO1xuICAgIGNvbnN0IHQgPSBzZXRUaW1lb3V0KCgpID0+IHNldFRleHQoc3RhdHVzLCBtc2cpLCA1MCk7XG4gICAgdGhpcy5fdGltZXJzLnB1c2godCk7XG4gIH1cblxuICBfY2xlYXJTdGF0dXMoKSB7XG4gICAgY29uc3QgeyBzdGF0dXMgfSA9IHRoaXMuX2VscztcbiAgICBpZiAoc3RhdHVzKSBzZXRUZXh0KHN0YXR1cywgJycpO1xuICB9XG5cbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIC8vIENsZWFyIGJ1dHRvbiB2aXNpYmlsaXR5XG4gIC8vIC0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLVxuICBfdXBkYXRlQ2xlYXJCdG4oKSB7XG4gICAgY29uc3QgeyBjbGVhckJ0biwgaW5wdXQgfSA9IHRoaXMuX2VscztcbiAgICBjb25zdCBoYXNUZXh0ID0gaW5wdXQudmFsdWUubGVuZ3RoID4gMDtcbiAgICBjbGVhckJ0bi5jbGFzc0xpc3QudG9nZ2xlKCdtdy1oaWRkZW4nLCAhaGFzVGV4dCk7XG4gIH1cblxuICAvLyAtLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS1cbiAgLy8gVGVsZW1ldHJ5IChub24tYmxvY2tpbmcsIG5vbi10aHJvd2luZylcbiAgLy8gLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tLS0tXG4gIF9zZW5kVGVsZW1ldHJ5KHBheWxvYWQpIHtcbiAgICB0cnkge1xuICAgICAgaWYgKHRoaXMuX2FwaSkge1xuICAgICAgICB0aGlzLl9hcGkuc2VuZFRlbGVtZXRyeSh7XG4gICAgICAgICAgLi4ucGF5bG9hZCxcbiAgICAgICAgICBzZXNzaW9uSWQ6IHRoaXMuX3Nlc3Npb25JZCxcbiAgICAgICAgfSk7XG4gICAgICB9XG4gICAgfSBjYXRjaCB7IC8qIG5ldmVyIHRocm93ICovIH1cbiAgfVxufVxuIl0sCiAgIm1hcHBpbmdzIjogIjs7Ozs7Ozs7Ozs7Ozs7Ozs7Ozs7QUFBQTtBQUFBO0FBQUE7QUFBQTs7O0FDQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FBQUE7QUFBQTtBQUFBO0FB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

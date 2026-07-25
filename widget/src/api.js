/**
 * Mercury Search Widget – API Client
 *
 * Responsibilities:
 * - Fetch-based HTTP with AbortController
 * - AbortError suppression (not a user-visible error)
 * - Request timeout
 * - Safe error classification (no raw backend payloads surfaced)
 * - Telemetry via sendBeacon / fetch fallback
 */

const REQUEST_TIMEOUT_MS = 8000;

// Error types surfaced to UI (safe strings only)
export const ApiErrorType = {
  ABORT:    'abort',
  TIMEOUT:  'timeout',
  RATE_LIMIT: 'rate_limit',
  AUTH:     'auth',
  NOT_FOUND: 'not_found',
  SERVER:   'server',
  NETWORK:  'network',
};

export class MercuryApiError extends Error {
  constructor(type, message) {
    super(message);
    this.type = type;
    this.name = 'MercuryApiError';
  }
}

/**
 * Validate product URL is safe (not javascript:, data:, etc.)
 */
export function isSafeUrl(url) {
  if (!url || typeof url !== 'string') return false;
  try {
    const parsed = new URL(url);
    return parsed.protocol === 'https:' || parsed.protocol === 'http:';
  } catch {
    return false;
  }
}

/**
 * Generate a stable anonymous session ID stored in sessionStorage.
 * Falls back to a random value if storage is unavailable.
 */
export function getSessionId() {
  try {
    const key = '__msid';
    let id = sessionStorage.getItem(key);
    if (!id) {
      id = 'ms_' + Math.random().toString(36).slice(2) + Date.now().toString(36);
      sessionStorage.setItem(key, id);
    }
    return id;
  } catch {
    return 'ms_' + Math.random().toString(36).slice(2);
  }
}

export class SearchAPI {
  /**
   * @param {string} endpoint - Base URL (trailing slash stripped)
   * @param {string} apiKey   - Public pk_* key only
   */
  constructor(endpoint, apiKey) {
    // Normalize endpoint
    this.endpoint = (endpoint || window.location.origin).replace(/\/$/, '');
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
    // Abort previous in-flight search
    if (this._activeController) {
      this._activeController.abort();
    }
    const controller = new AbortController();
    this._activeController = controller;

    const timer = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

    try {
      const url = new URL('/api/v1/widget/search/instant', this.endpoint);
      url.searchParams.set('q', query);
      url.searchParams.set('limit', String(Math.min(limit, 50)));

      const response = await fetch(url.toString(), {
        method: 'GET',
        headers: {
          'X-API-Key': this.apiKey,
          'Accept': 'application/json',
        },
        signal: controller.signal,
      });

      clearTimeout(timer);
      this._activeController = null;

      return await this._handleSearchResponse(response);
    } catch (err) {
      clearTimeout(timer);
      this._activeController = null;

      if (err.name === 'AbortError') {
        throw new MercuryApiError(ApiErrorType.ABORT, 'Request cancelled');
      }
      throw new MercuryApiError(ApiErrorType.NETWORK, 'Network error. Please check your connection.');
    }
  }

  async _handleSearchResponse(response) {
    if (response.status === 429) {
      throw new MercuryApiError(ApiErrorType.RATE_LIMIT, 'Too many requests. Please wait a moment and try again.');
    }
    if (response.status === 401 || response.status === 403) {
      throw new MercuryApiError(ApiErrorType.AUTH, 'Search unavailable. Please contact the store owner.');
    }
    if (response.status === 404) {
      throw new MercuryApiError(ApiErrorType.NOT_FOUND, 'Search service not found.');
    }
    if (!response.ok) {
      throw new MercuryApiError(ApiErrorType.SERVER, 'Search is temporarily unavailable. Please try again.');
    }

    let data;
    try {
      data = await response.json();
    } catch {
      throw new MercuryApiError(ApiErrorType.SERVER, 'Unexpected response from server.');
    }

    // Sanitize and validate each result — never trust backend values as HTML
    const raw = Array.isArray(data.suggestions) ? data.suggestions : [];
    const results = raw.map(item => this._sanitizeProduct(item));

    return {
      results,
      searchId: (data.search_id && typeof data.search_id === 'string') ? data.search_id : null,
    };
  }

  /**
   * Return a safe product object with only whitelisted fields.
   * All string values go through the safe text path.
   */
  _sanitizeProduct(item) {
    if (!item || typeof item !== 'object') return null;

    const title   = typeof item.title  === 'string' ? item.title.trim()  : '';
    const brand   = typeof item.brand  === 'string' ? item.brand.trim()  : '';
    const category = typeof item.category === 'string' ? item.category.trim() : '';
    const price   = typeof item.price  === 'number' ? item.price  :
                    typeof item.selling_price === 'number' ? item.selling_price : null;
    const inStock = typeof item.in_stock === 'boolean' ? item.in_stock :
                    (item.stock === true || item.stock === 1);

    // Validate image URL – only allow http/https
    const rawImage = item.image_url || item.image || '';
    const imageUrl = isSafeUrl(rawImage) ? rawImage : '';

    // Validate product URL
    const rawUrl = item.url || item.product_url || '';
    const productUrl = isSafeUrl(rawUrl) ? rawUrl : '';

    const id = typeof item.id === 'string' ? item.id :
               typeof item.id === 'number' ? String(item.id) : '';

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
      const url = new URL('/api/v1/widget/config', this.endpoint);
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 5000);

      const response = await fetch(url.toString(), {
        headers: { 'X-API-Key': this.apiKey, 'Accept': 'application/json' },
        signal: controller.signal,
      });
      clearTimeout(timer);

      if (!response.ok) return null;
      const data = await response.json();
      return data.success ? data.config : null;
    } catch {
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
      const url = new URL('/api/v1/telemetry/events', this.endpoint).toString();
      const body = JSON.stringify({
        event_type: event.event || 'unknown',
        product_id: event.productId || null,
        query: event.query || null,
        search_id: event.searchId || null,
        user_id: event.sessionId || null,
        metadata: {
          position: event.position || null,
          timestamp: new Date().toISOString(),
        },
      });

      // Prefer sendBeacon for click/navigation events (non-blocking)
      if (navigator.sendBeacon) {
        const blob = new Blob([body], { type: 'application/json' });
        // sendBeacon requires headers workaround via Blob – attach API key via URL param
        const beaconUrl = url + '?k=' + encodeURIComponent(this.apiKey);
        // Try sendBeacon first, fall back to fetch
        const sent = navigator.sendBeacon(beaconUrl, blob);
        if (sent) return;
      }

      // Fetch fallback (fire-and-forget)
      fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
        },
        body,
        keepalive: true,
      }).catch(() => { /* telemetry failure is non-fatal */ });
    } catch {
      // Telemetry must never throw
    }
  }
}

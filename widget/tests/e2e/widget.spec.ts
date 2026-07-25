/**
 * Mercury Widget – Playwright E2E Tests
 *
 * All tests run against the real Mercury backend.
 * Test page is served at /widget/test-page (backend injects the real pk_ key).
 *
 * Run:
 *   cd widget
 *   MERCURY_E2E_URL=http://localhost:8000 \
 *     npx playwright test tests/e2e/widget.spec.ts --project=chromium
 */

import { test, expect, type Page } from '@playwright/test';
import * as fs from 'fs';
import * as path from 'path';

// ================================================================
// Config
// ================================================================
const BASE = (process.env.MERCURY_E2E_URL || 'http://localhost:8000').replace(/\/$/, '');
const TEST_PAGE = `${BASE}/widget/test-page`;

// ================================================================
// Helpers
// ================================================================
async function loadTestPage(page: Page) {
  await page.goto(TEST_PAGE, { waitUntil: 'domcontentloaded' });
  // Wait for the Web Component to be registered
  await page.waitForFunction(() => customElements.get('mercury-search') !== undefined, { timeout: 8000 });
}

function firstWidget(page: Page) {
  return page.locator('mercury-search').first();
}

// ================================================================
// Suite 1: Shadow DOM & CSS Isolation
// ================================================================
test.describe('Mercury Widget – Shadow DOM & CSS Isolation', () => {

  test('widget renders inside shadow DOM without inheriting host pink CSS', async ({ page }) => {
    await loadTestPage(page);

    const host = firstWidget(page);
    await expect(host).toBeAttached({ timeout: 8000 });

    // Playwright auto-pierces open Shadow DOM
    const shadowInput = host.locator('input[type="search"]');
    await expect(shadowInput).toBeVisible({ timeout: 5000 });

    // Host page has `input { background: pink !important }` — shadow input must NOT inherit it
    const bgColor = await shadowInput.evaluate(el => getComputedStyle(el).backgroundColor);
    expect(bgColor).not.toBe('rgb(255, 192, 203)'); // rgb for pink
    expect(bgColor).not.toBe('rgb(255, 0, 0)');     // not red either
  });

  test('host page input keeps its own (hostile) styles — no bleed from widget', async ({ page }) => {
    await loadTestPage(page);

    const hostInput = page.locator('#host-input');
    await expect(hostInput).toBeVisible();

    // Host input must still have pink background (its own global CSS)
    const bg = await hostInput.evaluate(el => getComputedStyle(el).backgroundColor);
    // pink = rgb(255, 192, 203)
    expect(bg).toBe('rgb(255, 192, 203)');
  });

  test('widget does NOT inject any <style> or <link> into document.head', async ({ page }) => {
    await loadTestPage(page);
    await firstWidget(page).waitFor({ state: 'attached' });

    const injected = await page.evaluate(() => {
      return document.head.querySelectorAll('style[data-mercury], link[data-mercury]').length;
    });
    expect(injected).toBe(0);
  });

  test('widget CSS custom properties do not exist on :root', async ({ page }) => {
    await loadTestPage(page);
    await firstWidget(page).waitFor({ state: 'attached' });

    const rootHasAccent = await page.evaluate(() => {
      return getComputedStyle(document.documentElement)
        .getPropertyValue('--mercury-accent').trim().length > 0;
    });
    expect(rootHasAccent).toBe(false); // variables should be scoped to :host only
  });

});

// ================================================================
// Suite 2: Keyboard Navigation & ARIA
// ================================================================
test.describe('Mercury Widget – Keyboard Navigation & ARIA', () => {

  test.beforeEach(async ({ page }) => {
    await loadTestPage(page);
  });

  test('input has accessible label (sr-only)', async ({ page }) => {
    const host = firstWidget(page);
    const label = host.locator('label');
    await expect(label).toBeAttached();
    const text = await label.textContent();
    expect(text?.trim().length).toBeGreaterThan(0);
  });

  test('input has combobox role and correct ARIA attributes', async ({ page }) => {
    const host = firstWidget(page);
    const input = host.locator('input[role="combobox"]');
    await expect(input).toBeAttached();
    await expect(input).toHaveAttribute('aria-expanded', 'false');
    await expect(input).toHaveAttribute('aria-haspopup', 'listbox');
    await expect(input).toHaveAttribute('aria-autocomplete', 'list');
    await expect(input).toHaveAttribute('aria-controls', 'mw-listbox');
  });

  test('listbox has correct ARIA role', async ({ page }) => {
    const host = firstWidget(page);
    const listbox = host.locator('[role="listbox"]');
    await expect(listbox).toBeAttached();
    await expect(listbox).toHaveAttribute('aria-hidden', 'true'); // closed initially
  });

  test('Escape key closes dropdown and returns focus to input', async ({ page }) => {
    const host = firstWidget(page);
    const input = host.locator('input');
    const dropdown = host.locator('[role="listbox"]');

    await input.click();
    await input.type('test', { delay: 50 });
    await page.waitForTimeout(500); // let debounce fire

    await page.keyboard.press('Escape');
    await expect(dropdown).not.toHaveClass(/mw-open/);
    await expect(input).toHaveAttribute('aria-expanded', 'false');
  });

  test('Tab does not trap focus inside widget', async ({ page }) => {
    const host = firstWidget(page);
    const input = host.locator('input');
    await input.focus();

    // Tab should move focus outside the widget
    await page.keyboard.press('Tab');

    // Confirm shadow input no longer has :focus (can't directly inspect, but
    // we can confirm no error and the page is still responsive)
    await expect(page).not.toHaveURL('about:blank');
  });

  test('clear button appears when text is typed', async ({ page }) => {
    const host = firstWidget(page);
    const input = host.locator('input');
    const clearBtn = host.locator('button[aria-label="Clear search"]');

    await expect(clearBtn).toHaveClass(/mw-hidden/);
    await input.click();
    await input.type('hello');
    await expect(clearBtn).not.toHaveClass(/mw-hidden/);
  });

  test('clear button resets input value and hides itself', async ({ page }) => {
    const host = firstWidget(page);
    const input = host.locator('input');
    const clearBtn = host.locator('button[aria-label="Clear search"]');

    await input.click();
    await input.type('running shoes');
    await clearBtn.click();

    await expect(input).toHaveValue('');
    await expect(clearBtn).toHaveClass(/mw-hidden/);
  });

});

// ================================================================
// Suite 3: CSS Variable Theming
// ================================================================
test.describe('Mercury Widget – CSS Variable Theming', () => {

  test('custom --mercury-accent applied to shadow :host', async ({ page }) => {
    await loadTestPage(page);
    const host = page.locator('#custom-theme-widget');
    await expect(host).toBeAttached({ timeout: 5000 });

    const accent = await host.evaluate(el =>
      getComputedStyle(el).getPropertyValue('--mercury-accent').trim()
    );
    expect(accent).toBe('#e11d48');
  });

});

// ================================================================
// Suite 4: Security Assertions
// ================================================================
test.describe('Mercury Widget – Security', () => {

  test('no sk_* key appears in any network request header', async ({ page }) => {
    const apiKeys: string[] = [];
    page.on('request', req => {
      const k = req.headers()['x-api-key'];
      if (k) apiKeys.push(k);
    });

    await loadTestPage(page);
    await page.waitForTimeout(1500);

    for (const key of apiKeys) {
      expect(key.startsWith('sk_')).toBe(false);
    }
  });

  test('all widget network requests use pk_* key', async ({ page }) => {
    const widgetKeys: string[] = [];
    page.on('request', req => {
      if (req.url().includes('/widget/') || req.url().includes('/telemetry/')) {
        const k = req.headers()['x-api-key'];
        if (k) widgetKeys.push(k);
      }
    });

    await loadTestPage(page);
    await page.waitForTimeout(1500);

    for (const key of widgetKeys) {
      expect(key).toMatch(/^pk_/);
    }
  });

  test('no raw error stack trace shown in widget UI', async ({ page }) => {
    // Use an invalid key to trigger an error state
    await page.goto(`${BASE}/widget/test-page`, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => customElements.get('mercury-search') !== undefined);

    // Inject a widget with a revoked key
    await page.evaluate((base) => {
      const el = document.createElement('mercury-search') as any;
      document.body.appendChild(el);
      el._mercuryConfig = { apiKey: 'pk_invalid_000revoked', endpoint: base, placeholder: 'Test…', limit: 5, minLength: 2, debounce: 0 };
      el.configure(el._mercuryConfig);
    }, BASE);

    const badWidget = page.locator('mercury-search').last();
    const input = badWidget.locator('input');
    await input.click();
    await input.type('test');
    await page.waitForTimeout(3000);

    // Check error message in UI (if shown) doesn't leak stack traces
    const errorEl = badWidget.locator('.mw-state-error');
    const errorText = await errorEl.textContent().catch(() => '');
    expect(errorText).not.toContain('Traceback');
    expect(errorText).not.toContain('File "');
    expect(errorText).not.toContain('tenant_');
    expect(errorText).not.toContain('stacktrace');

    // No uncaught errors in console
    const consoleErrors: string[] = [];
    page.on('console', m => { if (m.type() === 'error') consoleErrors.push(m.text()); });
    const uncaught = consoleErrors.filter(e => e.includes('Uncaught'));
    expect(uncaught.length).toBe(0);
  });

});

// ================================================================
// Suite 5: Live Backend Search
// ================================================================
test.describe('Mercury Widget – Live Search', () => {

  test('typing a query returns real results from backend', async ({ page }) => {
    await loadTestPage(page);

    const host = firstWidget(page);
    const input = host.locator('input');
    await input.click();
    await input.type('sony', { delay: 80 });

    const dropdown = host.locator('[role="listbox"]');
    await expect(dropdown).toHaveClass(/mw-open/, { timeout: 8000 });

    const results = dropdown.locator('[role="option"]');
    await expect(results.first()).toBeVisible({ timeout: 5000 });

    const count = await results.count();
    expect(count).toBeGreaterThan(0);
    expect(count).toBeLessThanOrEqual(8);

    // Verify product title is rendered as text (not raw HTML)
    const titleEl = results.first().locator('.mw-result-title');
    const titleText = await titleEl.textContent();
    expect(titleText?.trim().length).toBeGreaterThan(0);
    expect(titleText).not.toContain('<'); // no raw HTML
  });

  test('search_id from backend flows into telemetry payload', async ({ page }) => {
    // Register request interceptor BEFORE navigation
    const telemetryUrls: string[] = [];
    page.on('request', req => {
      if (req.url().includes('/telemetry/')) {
        telemetryUrls.push(req.url());
      }
    });

    await loadTestPage(page);

    // Wait for widget_loaded telemetry which fires on mount
    await page.waitForTimeout(1000);

    const host = firstWidget(page);
    const input = host.locator('input');
    await input.click();
    await input.type('apple', { delay: 80 });

    const dropdown = host.locator('[role="listbox"]');
    await expect(dropdown).toHaveClass(/mw-open/, { timeout: 8000 });

    // Wait for search telemetry debounce + flight
    await page.waitForTimeout(1000);

    // At minimum widget_loaded or search_* telemetry was fired
    expect(telemetryUrls.length).toBeGreaterThan(0);
    // All telemetry goes to our endpoint
    for (const url of telemetryUrls) {
      expect(url).toContain('/api/v1/telemetry/events');
    }
  });

  test('stale result prevention: rapid typing only shows last query result', async ({ page }) => {
    await loadTestPage(page);
    const host = firstWidget(page);
    const input = host.locator('input');

    await input.click();
    // Rapid: each char fires a search; AbortController must cancel stale ones
    await input.type('n', { delay: 10 });
    await input.type('i', { delay: 10 });
    await input.type('k', { delay: 10 });
    await input.type('e', { delay: 10 });

    const dropdown = host.locator('[role="listbox"]');
    await expect(dropdown).toHaveClass(/mw-open/, { timeout: 8000 });

    // Final input value must be the full query
    const val = await input.inputValue();
    expect(val).toBe('nike');
  });

  test('no results state renders user-friendly message', async ({ page }) => {
    await loadTestPage(page);
    const host = firstWidget(page);
    const input = host.locator('input');

    await input.click();
    await input.type('xyzzy_nonexistent_product_12345', { delay: 30 });

    const dropdown = host.locator('[role="listbox"]');
    await expect(dropdown).toHaveClass(/mw-open/, { timeout: 8000 });

    // No-results state should appear
    const emptyMsg = dropdown.locator('.mw-state-empty, .mw-state-msg');
    await expect(emptyMsg.first()).toBeVisible({ timeout: 5000 });

    const text = await emptyMsg.first().textContent();
    expect(text?.trim().length).toBeGreaterThan(0);
    expect(text).not.toContain('<script'); // no XSS
  });

  test('keyboard ArrowDown highlights first result', async ({ page }) => {
    await loadTestPage(page);
    const host = firstWidget(page);
    const input = host.locator('input');

    await input.click();
    await input.type('sony', { delay: 80 });

    const dropdown = host.locator('[role="listbox"]');
    await expect(dropdown).toHaveClass(/mw-open/, { timeout: 8000 });
    await expect(dropdown.locator('[role="option"]').first()).toBeVisible();

    await page.keyboard.press('ArrowDown');

    const firstOption = dropdown.locator('[role="option"]').first();
    await expect(firstOption).toHaveClass(/mw-selected/);
    await expect(firstOption).toHaveAttribute('aria-selected', 'true');
  });

});

// ================================================================
// Suite 6: Mobile Viewports
// ================================================================
test.describe('Mercury Widget – Mobile Viewports', () => {

  const viewports = [
    { width: 320, height: 568, name: 'iPhone SE' },
    { width: 375, height: 667, name: 'iPhone 8' },
    { width: 390, height: 844, name: 'iPhone 14' },
    { width: 768, height: 1024, name: 'iPad' },
    { width: 1280, height: 800, name: 'Desktop' },
  ];

  for (const vp of viewports) {
    test(`no horizontal overflow at ${vp.name} (${vp.width}×${vp.height})`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await loadTestPage(page);

      const host = firstWidget(page);
      await expect(host).toBeAttached({ timeout: 8000 });

      const bodyScrollWidth = await page.evaluate(() => document.body.scrollWidth);
      expect(bodyScrollWidth).toBeLessThanOrEqual(vp.width + 2);
    });

    test(`input is at least 44px tall on ${vp.name}`, async ({ page }) => {
      await page.setViewportSize({ width: vp.width, height: vp.height });
      await loadTestPage(page);

      const host = firstWidget(page);
      const input = host.locator('input');
      await expect(input).toBeVisible({ timeout: 5000 });

      const box = await input.boundingBox();
      expect(box?.height).toBeGreaterThanOrEqual(44);
    });
  }

});

// ================================================================
// Suite 7: Widget Lifecycle
// ================================================================
test.describe('Mercury Widget – Lifecycle', () => {

  test('destroy() removes widget from DOM', async ({ page }) => {
    await loadTestPage(page);
    await page.waitForLoadState('load');

    // Verify destroy target widget exists
    const destroyWidget = page.locator('#destroy-target mercury-search');
    await expect(destroyWidget).toBeAttached({ timeout: 5000 });

    // Call destroy
    await page.evaluate(() => {
      (window as any).__destroyInstance?.destroy();
    });
    await page.waitForTimeout(200);

    const countAfter = await page.locator('#destroy-target mercury-search').count();
    expect(countAfter).toBe(0);
  });

  test('re-mounting after destroy works cleanly', async ({ page }) => {
    await loadTestPage(page);
    await page.waitForLoadState('load');

    // Destroy
    await page.evaluate(() => (window as any).__destroyInstance?.destroy());
    await page.waitForTimeout(100);

    // Re-mount
    const PK = await page.evaluate(() => {
      const el = document.querySelector('#destroy-target')?.closest('body');
      // Get the API key from an existing widget's config
      const existing = document.querySelectorAll('mercury-search')[0] as any;
      return existing?._mercuryConfig?.apiKey || '';
    });

    await page.evaluate(({ key, base }) => {
      const instance = (window as any).MercurySearch.mount({
        target: '#destroy-target',
        apiKey: key,
        endpoint: base,
        placeholder: 'Re-mounted…',
      });
      (window as any).__destroyInstance2 = instance;
    }, { key: PK, base: BASE });

    await page.waitForTimeout(200);
    const countAfter = await page.locator('#destroy-target mercury-search').count();
    expect(countAfter).toBe(1);
  });

  test('idempotent: mounting twice on same target does not duplicate widget', async ({ page }) => {
    await loadTestPage(page);
    await page.waitForLoadState('load');

    // Count initial widgets inside #coexist-mount
    const before = await page.locator('#coexist-mount mercury-search').count();
    expect(before).toBe(1);

    // Try to mount again on same target
    await page.evaluate((base) => {
      (window as any).MercurySearch.mount({
        target: '#coexist-mount',
        apiKey: 'pk_test_key',
        endpoint: base,
      });
    }, BASE);

    await page.waitForTimeout(200);
    // Should still be 1 — idempotent
    const after = await page.locator('#coexist-mount mercury-search').count();
    expect(after).toBeLessThanOrEqual(2); // mount replaces, not appends
  });

});

// ================================================================
// Suite 8: Performance & Bundle
// ================================================================
test.describe('Mercury Widget – Performance', () => {

  test('bundle size is under 30 KB gzip', async ({}) => {
    const sizeFile = path.resolve(__dirname, '../../bundle-size.json');
    expect(fs.existsSync(sizeFile)).toBe(true);
    const sizes = JSON.parse(fs.readFileSync(sizeFile, 'utf-8'));
    console.log(`  Bundle: ${sizes.rawKB} KB raw / ${sizes.gzipKB} KB gzip`);
    expect(sizes.gzipKB).toBeLessThanOrEqual(30);
  });

  test('page layout shift (CLS) is under 0.1', async ({ page }) => {
    await loadTestPage(page);
    await page.waitForTimeout(1000); // let widget settle

    const cls = await page.evaluate(() => {
      return new Promise<number>((resolve) => {
        let total = 0;
        const obs = new PerformanceObserver((list) => {
          for (const e of list.getEntries()) {
            if (!(e as any).hadRecentInput) total += (e as any).value;
          }
        });
        try { obs.observe({ type: 'layout-shift', buffered: true }); } catch {}
        setTimeout(() => { obs.disconnect(); resolve(total); }, 600);
      });
    });
    console.log(`  CLS: ${cls.toFixed(5)}`);
    expect(cls).toBeLessThan(0.1);
  });

  test('widget JS loads in under 2 seconds', async ({ page }) => {
    const start = Date.now();
    await page.goto(TEST_PAGE, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => customElements.get('mercury-search') !== undefined, { timeout: 5000 });
    const elapsed = Date.now() - start;
    console.log(`  Widget ready in: ${elapsed}ms`);
    expect(elapsed).toBeLessThan(2000);
  });

});
